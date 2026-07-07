#!/usr/bin/env python3
"""
analyze_angular.py - lightweight, compile-free static analyzer for an Angular
frontend. Emits a JSON model:

  - files with a kind (component/service/module/directive/pipe/other) + classes
  - importEdges: resolved relative-import graph (from -> to)
  - externalImports: bare module specifiers (e.g. @angular/core)
  - httpCalls: every HttpClient call with its (normalized) URL and verb
  - components / services / modules: convenience file lists

Heuristic by design. For a richer import graph, escalate to `npx madge`
(see references/methodology.md).

Usage:
  python analyze_angular.py --root <angular-src-dir> --out frontend.json
         [--include-tests] [--pretty]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", ".git", ".angular", "coverage", "out-tsc"}
MAX_FILE_BYTES = 2_000_000

RE_IMPORT_FROM = re.compile(
    r'import\s+(?:type\s+)?(?:[\w*\{\}\,\s]+?)\s+from\s+[\'"]([^\'"]+)[\'"]'
)
RE_IMPORT_SIDE = re.compile(r'import\s+[\'"]([^\'"]+)[\'"]')
RE_EXPORT_CLASS = re.compile(r'export\s+(?:abstract\s+)?class\s+([A-Za-z0-9_]+)')
RE_HTTP_CALL = re.compile(
    r'\.(get|post|put|delete|patch)\s*(?:<[^>{};]*>)?\(\s*([`\'"])((?:\\.|(?!\2).)*)\2',
    re.IGNORECASE,
)

DECORATORS = {
    "@Component": "component",
    "@Injectable": "service",
    "@NgModule": "module",
    "@Directive": "directive",
    "@Pipe": "pipe",
}


def rel(path, root):
    try:
        return os.path.relpath(str(path), root).replace(os.sep, "/")
    except ValueError:
        return str(path).replace(os.sep, "/")


def iter_ts(root, include_tests):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".ts"):
                continue
            if fn.endswith(".d.ts"):
                continue
            if not include_tests and (fn.endswith(".spec.ts") or fn.endswith(".test.ts")):
                continue
            yield Path(dirpath) / fn


def read_text(path):
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def resolve_import(spec, from_file, known_files):
    """Resolve a relative import specifier to a known file (posix rel path)."""
    if not spec.startswith("."):
        return None
    base = os.path.dirname(from_file)
    target = os.path.normpath(os.path.join(base, spec)).replace(os.sep, "/")
    candidates = [
        target,
        target + ".ts",
        target + "/index.ts",
    ]
    for c in candidates:
        if c in known_files:
            return c
    # strip an explicit .ts the author may have written
    if target.endswith(".ts") and target in known_files:
        return target
    return None


def normalize_url(url):
    """Reduce a captured URL literal to a comparable path template."""
    u = url.strip()
    # strip protocol + host
    m = re.match(r'^[a-zA-Z]+://[^/]+(/.*)$', u)
    if m:
        u = m.group(1)
    # drop query / fragment
    u = re.split(r'[?#]', u)[0]
    # template-literal and concatenation params -> *
    u = re.sub(r'\$\{[^}]*\}', "*", u)
    u = u.replace("`", "").replace("'", "").replace('"', "")
    # a leading ${base}/ becomes /*/... ; collapse a leading '*' base segment
    u = u.strip()
    if not u.startswith("/"):
        # if it starts with a wildcard base like */api/... keep from first real segment
        u = "/" + u.lstrip("/")
    # numeric / guid-ish segments -> *
    segs = []
    for seg in u.split("/"):
        if seg == "":
            continue
        if re.fullmatch(r'\*+', seg):
            segs.append("*")
        elif re.fullmatch(r'\d+', seg):
            segs.append("*")
        elif re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F-]{20,}', seg):
            segs.append("*")
        else:
            segs.append(seg.lower())
    return "/" + "/".join(segs)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Static analyzer for an Angular frontend.")
    ap.add_argument("--root", required=True, help="Frontend source directory.")
    ap.add_argument("--out", required=True, help="Output JSON path.")
    ap.add_argument("--include-tests", action="store_true")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args(argv)

    root = str(Path(args.root).resolve())
    if not os.path.isdir(root):
        print("error: --root is not a directory: " + root, file=sys.stderr)
        return 2

    files_meta = {}
    raw = {}
    for ts in iter_ts(root, args.include_tests):
        text = read_text(ts)
        if text == "":
            continue
        rp = rel(ts, root)
        raw[rp] = text

    known = set(raw.keys())
    import_edges, external_imports, http_calls = [], [], []
    components, services, modules = [], [], []

    for rp, text in raw.items():
        kind = "other"
        for dec, k in DECORATORS.items():
            if dec in text:
                kind = k
                break
        classes = RE_EXPORT_CLASS.findall(text)
        files_meta[rp] = {"path": rp, "kind": kind, "classes": classes}
        if kind == "component":
            components.append(rp)
        elif kind == "service":
            services.append(rp)
        elif kind == "module":
            modules.append(rp)

        specs = set(RE_IMPORT_FROM.findall(text)) | set(RE_IMPORT_SIDE.findall(text))
        for spec in specs:
            resolved = resolve_import(spec, rp, known)
            if resolved:
                import_edges.append({"from": rp, "to": resolved})
            elif not spec.startswith("."):
                external_imports.append({"from": rp, "module": spec})

        for hm in RE_HTTP_CALL.finditer(text):
            method = hm.group(1).upper()
            url_raw = hm.group(3)
            if "/" not in url_raw and "${" not in url_raw:
                continue  # not an API path
            http_calls.append({
                "file": rp,
                "method": method,
                "url": normalize_url(url_raw),
                "rawUrl": url_raw.strip(),
            })

    model = {
        "root": root,
        "stack": "angular",
        "files": list(files_meta.values()),
        "importEdges": import_edges,
        "externalImports": external_imports,
        "httpCalls": http_calls,
        "components": components,
        "services": services,
        "modules": modules,
        "summary": {
            "files": len(files_meta),
            "importEdges": len(import_edges),
            "httpCalls": len(http_calls),
            "components": len(components),
            "services": len(services),
        },
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2 if args.pretty else None)
    s = model["summary"]
    print("angular: {files} files, {importEdges} import edges, {httpCalls} HTTP "
          "calls, {components} components -> {out}".format(out=args.out, **s), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
