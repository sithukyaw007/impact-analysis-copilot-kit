#!/usr/bin/env python3
"""
analyze_dotnet.py - lightweight, compile-free static analyzer for a .NET (Core)
backend. Emits a JSON dependency model:

  - projects, project references, package references (from *.csproj)
  - API endpoints (controller [Route] + action Http* routes, with verbs)
  - defined types (class/record/interface/enum/struct) and their file
  - DI edges (constructor-injected dependency types)
  - typeReferences: which files mention each project-defined type

Heuristic by design (no Roslyn / MSBuild). For compiler-accurate fidelity see
references/methodology.md.

Usage:
  python analyze_dotnet.py --root <backend-src-dir> --out backend.json [--pretty]
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SKIP_DIRS = {"bin", "obj", ".git", ".vs", "node_modules", "dist", "packages"}
MAX_FILE_BYTES = 2_000_000

HTTP_ATTRS = {
    "HttpGet": "GET", "HttpPost": "POST", "HttpPut": "PUT",
    "HttpDelete": "DELETE", "HttpPatch": "PATCH",
    "HttpHead": "HEAD", "HttpOptions": "OPTIONS",
}

RE_NAMESPACE = re.compile(r'\bnamespace\s+([A-Za-z0-9_.]+)')
RE_TYPE_DECL = re.compile(r'\b(class|record|interface|enum|struct)\s+([A-Za-z0-9_]+)')
RE_ROUTE_ATTR = re.compile(r'\[\s*Route\s*\(\s*"([^"]*)"')
RE_HTTP_ATTR = re.compile(
    r'\[\s*(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch|HttpHead|HttpOptions)\s*(?:\(\s*"([^"]*)")?'
)
RE_CLASS_HEADER = re.compile(r'\bclass\s+([A-Za-z0-9_]+)\s*(:[^\{]*)?\{')


def rel(path, root):
    try:
        return os.path.relpath(str(path), root).replace(os.sep, "/")
    except ValueError:
        return str(path).replace(os.sep, "/")


def iter_files(root, suffix):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(suffix):
                yield Path(dirpath) / fn


def read_text(path):
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def parse_csproj(root):
    projects, proj_refs, pkg_refs, proj_dirs = [], [], [], []
    for csproj in iter_files(root, ".csproj"):
        name = csproj.stem
        projects.append({"name": name, "path": rel(csproj, root)})
        proj_dirs.append((str(csproj.parent), name))
        text = read_text(csproj)
        if not text:
            continue
        try:
            tree = ET.ElementTree(ET.fromstring(text))
        except ET.ParseError:
            continue
        for node in tree.iter():
            tag = node.tag.split("}")[-1]
            if tag == "ProjectReference":
                inc = node.get("Include", "").replace("\\", "/")
                if inc:
                    proj_refs.append({"from": name, "to": Path(inc).stem})
            elif tag == "PackageReference":
                pkg = node.get("Include", "")
                if pkg:
                    pkg_refs.append({
                        "project": name,
                        "package": pkg,
                        "version": node.get("Version", ""),
                    })
    # deepest matching project dir wins
    proj_dirs.sort(key=lambda p: len(p[0]), reverse=True)
    return projects, proj_refs, pkg_refs, proj_dirs


def project_for(file_path, proj_dirs):
    fp = str(file_path)
    for pdir, name in proj_dirs:
        if fp.startswith(pdir + os.sep) or fp.startswith(pdir + "/"):
            return name
    return None


def combine_route(class_route, method_route, controller, action):
    def norm(tok):
        if tok is None:
            return None
        base = controller[:-10] if controller and controller.endswith("Controller") else (controller or "")
        tok = tok.replace("[controller]", base)
        tok = tok.replace("[action]", action or "")
        return tok
    class_route = norm(class_route)
    method_route = norm(method_route)
    if method_route and (method_route.startswith("/") or method_route.startswith("~/")):
        path = method_route.lstrip("~")
    else:
        parts = [seg.strip("/") for seg in (class_route, method_route) if seg]
        path = "/" + "/".join(p for p in parts if p)
    if not path.startswith("/"):
        path = "/" + path
    return path or "/"


def analyze_cs(text):
    """Return (types, endpoints, di_edges) for one .cs file's text."""
    types = [{"kind": m.group(1), "name": m.group(2)} for m in RE_TYPE_DECL.finditer(text)]

    # Class positions + their route (from a window before the declaration).
    classes = []
    for cm in RE_CLASS_HEADER.finditer(text):
        name = cm.group(1)
        bases = cm.group(2) or ""
        window = text[max(0, cm.start() - 500):cm.start()]
        route = None
        routes = RE_ROUTE_ATTR.findall(window)
        if routes:
            route = routes[-1]
        is_ctrl = (
            name.endswith("Controller")
            or "ApiController" in window
            or bool(re.search(r'Controller(Base)?\b', bases))
        )
        classes.append({"pos": cm.start(), "name": name, "route": route, "is_controller": is_ctrl})
    classes.sort(key=lambda c: c["pos"])

    def controller_for(pos):
        cur = None
        for c in classes:
            if c["pos"] > pos:
                break
            if c["is_controller"]:
                cur = c
        return cur

    endpoints = []
    for hm in RE_HTTP_ATTR.finditer(text):
        verb = HTTP_ATTRS.get(hm.group(1))
        mroute = hm.group(2)
        after = text[hm.end():hm.end() + 400]
        am = re.search(
            r'(?:\[[^\]]*\]\s*)*(?:public|private|protected|internal)[^\n;{}]*?\b([A-Za-z0-9_]+)\s*\(',
            after,
        )
        action = am.group(1) if am else None
        ctrl = controller_for(hm.start())
        cname = ctrl["name"] if ctrl else None
        croute = ctrl["route"] if ctrl else None
        endpoints.append({
            "method": verb,
            "path": combine_route(croute, mroute, cname, action),
            "controller": cname,
            "action": action,
        })

    # DI edges: constructor params (public <ClassName>( ... )).
    di_edges = []
    for c in classes:
        cm = re.search(
            r'public\s+' + re.escape(c["name"]) + r'\s*\(([^)]*)\)',
            text,
        )
        if not cm:
            continue
        params = cm.group(1).strip()
        if not params:
            continue
        for part in params.split(","):
            tokens = part.strip().split()
            if len(tokens) >= 2:
                ptype = re.sub(r'<.*', "", tokens[0]).strip()
                if ptype:
                    di_edges.append({"from": c["name"], "toType": ptype})
    return types, endpoints, di_edges


def main(argv=None):
    ap = argparse.ArgumentParser(description="Static analyzer for a .NET backend.")
    ap.add_argument("--root", required=True, help="Backend source directory.")
    ap.add_argument("--out", required=True, help="Output JSON path.")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args(argv)

    root = str(Path(args.root).resolve())
    if not os.path.isdir(root):
        print("error: --root is not a directory: " + root, file=sys.stderr)
        return 2

    projects, proj_refs, pkg_refs, proj_dirs = parse_csproj(root)

    all_types, endpoints, di_edges = [], [], []
    file_texts = {}  # rel path -> text (for typeReferences pass)
    type_def_file = {}

    for cs in iter_files(root, ".cs"):
        if cs.name.endswith((".g.cs", ".Designer.cs", ".AssemblyInfo.cs")):
            continue
        text = read_text(cs)
        if not text:
            continue
        rp = rel(cs, root)
        file_texts[rp] = text
        proj = project_for(cs, proj_dirs)
        namespace = None
        nm = RE_NAMESPACE.search(text)
        if nm:
            namespace = nm.group(1)
        types, eps, dis = analyze_cs(text)
        for t in types:
            t.update({"file": rp, "project": proj, "namespace": namespace})
            all_types.append(t)
            type_def_file.setdefault(t["name"], rp)
        for e in eps:
            e.update({"file": rp, "project": proj})
            endpoints.append(e)
        for d in dis:
            d.update({"file": rp})
            di_edges.append(d)

    # typeReferences: which files mention each defined type (word-boundary).
    type_refs = {}
    type_names = [t["name"] for t in all_types]
    if 0 < len(type_names) <= 4000:
        uniq = sorted(set(type_names), key=len, reverse=True)
        big = re.compile(r'\b(' + "|".join(re.escape(n) for n in uniq) + r')\b')
        for rp, text in file_texts.items():
            found = set(big.findall(text))
            for name in found:
                if type_def_file.get(name) == rp and text.count(name) <= 1:
                    continue
                type_refs.setdefault(name, [])
                if rp not in type_refs[name]:
                    type_refs[name].append(rp)

    model = {
        "root": root,
        "stack": "dotnet",
        "projects": projects,
        "projectReferences": proj_refs,
        "packageReferences": pkg_refs,
        "endpoints": endpoints,
        "types": all_types,
        "diEdges": di_edges,
        "typeReferences": type_refs,
        "summary": {
            "projects": len(projects),
            "endpoints": len(endpoints),
            "types": len(all_types),
            "diEdges": len(di_edges),
        },
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2 if args.pretty else None)
    s = model["summary"]
    print("dotnet: {projects} projects, {endpoints} endpoints, {types} types, "
          "{diEdges} DI edges -> {out}".format(out=args.out, **s), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
