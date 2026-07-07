#!/usr/bin/env python3
"""
impact_of_change.py - the entry point of the impact-analysis engine.

Given a changed type, file, or endpoint, it computes the downstream blast radius
across BOTH the Angular frontend and the .NET backend, and writes:
  - impact.json  (machine-readable)
  - impact.md    (human-readable report)

It orchestrates the other three scripts, (re)generating backend.json,
frontend.json and links.json under --out if they are missing or --refresh is set.

Usage:
  python impact_of_change.py --frontend <angular-src> --backend <dotnet-src>
                 --changed "CustomerDto" --out ./.impact-out/<scope> [--refresh] [--pretty]

--changed accepts a type/class name, a file path, or an endpoint path
(e.g. "CustomerDto", "order.service.ts", "/api/orders/{id}").
"""
import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAX_NODES = 500
MAX_DEPTH = 8
LIST_CAP = 50


def run_step(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr.decode("utf-8", "ignore"))
        raise SystemExit("step failed: " + " ".join(str(c) for c in cmd))


def ensure_models(frontend_src, backend_src, out, refresh, python):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    backend_json = out / "backend.json"
    frontend_json = out / "frontend.json"
    links_json = out / "links.json"
    if refresh or not backend_json.exists():
        run_step([python, str(HERE / "analyze_dotnet.py"), "--root", backend_src,
                  "--out", str(backend_json)])
    if refresh or not frontend_json.exists():
        run_step([python, str(HERE / "analyze_angular.py"), "--root", frontend_src,
                  "--out", str(frontend_json)])
    if refresh or not links_json.exists():
        run_step([python, str(HERE / "link_cross_stack.py"), "--backend", str(backend_json),
                  "--frontend", str(frontend_json), "--out", str(links_json)])
    return (json.loads(backend_json.read_text(encoding="utf-8")),
            json.loads(frontend_json.read_text(encoding="utf-8")),
            json.loads(links_json.read_text(encoding="utf-8")))


def reverse_import_closure(import_edges, seeds):
    radj = defaultdict(set)
    for e in import_edges:
        radj[e["to"]].add(e["from"])
    seen = set(seeds)
    q = deque((s, 0) for s in seeds)
    order = []
    while q and len(seen) < MAX_NODES:
        node, depth = q.popleft()
        if depth >= MAX_DEPTH:
            continue
        for dep in radj.get(node, ()):
            if dep not in seen:
                seen.add(dep)
                order.append(dep)
                q.append((dep, depth + 1))
    return order


def classify(changed, backend, frontend):
    types_by_name = defaultdict(list)
    for t in backend.get("types", []):
        types_by_name[t["name"]].append(t)
    backend_files = {t["file"] for t in backend.get("types", [])}
    backend_files |= {e["file"] for e in backend.get("endpoints", []) if e.get("file")}
    frontend_files = {f["path"] for f in frontend.get("files", [])}
    fe_class_to_file = {}
    for f in frontend.get("files", []):
        for c in f.get("classes", []):
            fe_class_to_file[c] = f["path"]
    endpoints = backend.get("endpoints", [])

    chg = changed.strip()
    low = chg.lower()

    # 1) endpoint path (resolve to the canonical stored path when possible)
    if chg.startswith("/"):
        for ep in endpoints:
            if (ep.get("path") or "").lower() == low:
                return {"kind": "endpoint", "value": ep.get("path")}
        return {"kind": "endpoint", "value": chg}
    for ep in endpoints:
        if (ep.get("path") or "").lower() == low:
            return {"kind": "endpoint", "value": ep.get("path")}

    # 2) backend type name (exact, then case-insensitive)
    if chg in types_by_name:
        return {"kind": "backend_type", "types": [chg],
                "files": [t["file"] for t in types_by_name[chg]]}
    for name in types_by_name:
        if name.lower() == low:
            return {"kind": "backend_type", "types": [name],
                    "files": [t["file"] for t in types_by_name[name]]}

    # 3) backend file
    if chg.endswith(".cs"):
        hit = [bf for bf in backend_files if bf.endswith(chg) or os.path.basename(bf) == os.path.basename(chg)]
        types_in = [t["name"] for t in backend.get("types", []) if t["file"] in hit]
        return {"kind": "backend_file", "files": hit, "types": types_in}

    # 4) frontend file
    if chg.endswith(".ts"):
        hit = [ff for ff in frontend_files if ff.endswith(chg) or os.path.basename(ff) == os.path.basename(chg)]
        return {"kind": "frontend_file", "files": hit}

    # 5) frontend class name
    if chg in fe_class_to_file:
        return {"kind": "frontend_file", "files": [fe_class_to_file[chg]]}
    for c, f in fe_class_to_file.items():
        if c.lower() == low:
            return {"kind": "frontend_file", "files": [f]}

    # 6) fuzzy filename contains
    fhit = [bf for bf in backend_files if low in bf.lower()]
    if fhit:
        types_in = [t["name"] for t in backend.get("types", []) if t["file"] in fhit]
        return {"kind": "backend_file", "files": fhit, "types": types_in}
    fehit = [ff for ff in frontend_files if low in ff.lower()]
    if fehit:
        return {"kind": "frontend_file", "files": fehit}

    return {"kind": "unknown", "value": chg}


def backend_type_impact(changed_types, seed_files, backend, links):
    type_refs = backend.get("typeReferences", {})
    type_file = {}
    for t in backend.get("types", []):
        type_file.setdefault(t["name"], t["file"])
    class_file = dict(type_file)

    affected_files = set(seed_files)
    affected_types = set(changed_types)

    # files that reference the changed types
    for t in changed_types:
        for f in type_refs.get(t, []):
            affected_files.add(f)
        if t in type_file:
            affected_files.add(type_file[t])

    # reverse DI: classes that inject a changed type (one hop)
    for e in backend.get("diEdges", []):
        if e.get("toType") in affected_types:
            affected_types.add(e["from"])
            if e["from"] in class_file:
                affected_files.add(class_file[e["from"]])
            if e.get("file"):
                affected_files.add(e["file"])

    # endpoints in affected files or affected controllers
    affected_endpoints = []
    for ep in backend.get("endpoints", []):
        if ep.get("file") in affected_files or ep.get("controller") in affected_types:
            affected_endpoints.append(ep)

    ep_keys = {(ep.get("method"), ep.get("path")) for ep in affected_endpoints}
    cross = []
    for ce in links.get("crossEdges", []):
        if (ce.get("method"), ce.get("endpointPath")) in ep_keys or ce.get("backendFile") in affected_files:
            cross.append(ce)
    frontend_seeds = sorted({ce["frontendFile"] for ce in cross if ce.get("frontendFile")})
    return affected_files, affected_types, affected_endpoints, cross, frontend_seeds


def build_report(changed, cls, backend, frontend, links):
    md = ["# Impact analysis: `{}`".format(changed), ""]
    data = {"changed": changed, "classifiedAs": cls["kind"]}

    def section(title, items, fmt):
        md.append("## " + title + " ({})".format(len(items)))
        if not items:
            md.append("_none found_")
        else:
            for it in items[:LIST_CAP]:
                md.append("- " + fmt(it))
            if len(items) > LIST_CAP:
                md.append("- _...and {} more_".format(len(items) - LIST_CAP))
        md.append("")

    if cls["kind"] in ("backend_type", "backend_file"):
        changed_types = cls.get("types", [])
        seed_files = cls.get("files", [])
        (aff_files, aff_types, aff_eps, cross, fe_seeds) = backend_type_impact(
            changed_types, seed_files, backend, links)
        fe_closure = reverse_import_closure(frontend.get("importEdges", []), fe_seeds)

        md.append("**Classified as a backend change.** Changed types: "
                  + (", ".join("`%s`" % t for t in changed_types) or "_(file-level)_"))
        md.append("")
        section("Backend files affected", sorted(aff_files), lambda x: "`%s`" % x)
        section("Backend API endpoints affected",
                aff_eps, lambda e: "`{} {}` ({}.{})".format(
                    e.get("method"), e.get("path"), e.get("controller"), e.get("action")))
        section("Cross-stack call paths", cross,
                lambda c: "`{}` -> `{} {}` -> `{}.{}` _(match: {})_".format(
                    c.get("frontendFile"), c.get("method"), c.get("endpointPath"),
                    c.get("controller"), c.get("action"), c.get("confidence")))
        section("Frontend files affected (reverse-import closure)",
                sorted(set(fe_seeds) | set(fe_closure)), lambda x: "`%s`" % x)

        data.update({
            "backendFilesAffected": sorted(aff_files),
            "endpointsAffected": aff_eps,
            "crossStackPaths": cross,
            "frontendFilesAffected": sorted(set(fe_seeds) | set(fe_closure)),
        })

    elif cls["kind"] == "frontend_file":
        seeds = cls.get("files", [])
        closure = reverse_import_closure(frontend.get("importEdges", []), seeds)
        calls = [ce for ce in links.get("crossEdges", []) if ce.get("frontendFile") in set(seeds)]
        md.append("**Classified as a frontend change.** Seed files: "
                  + ", ".join("`%s`" % s for s in seeds))
        md.append("")
        section("Frontend files affected (reverse-import closure)",
                sorted(set(seeds) | set(closure)), lambda x: "`%s`" % x)
        section("Backend endpoints this code depends on", calls,
                lambda c: "`{} {}` -> `{}.{}`".format(
                    c.get("method"), c.get("endpointPath"), c.get("controller"), c.get("action")))
        data.update({
            "frontendFilesAffected": sorted(set(seeds) | set(closure)),
            "backendEndpointsDependedOn": calls,
        })

    elif cls["kind"] == "endpoint":
        path = cls["value"]
        lp = path.lower()
        eps = [e for e in backend.get("endpoints", []) if (e.get("path") or "").lower() == lp]
        cross = [ce for ce in links.get("crossEdges", []) if (ce.get("endpointPath") or "").lower() == lp]
        fe_seeds = sorted({ce["frontendFile"] for ce in cross if ce.get("frontendFile")})
        closure = reverse_import_closure(frontend.get("importEdges", []), fe_seeds)
        md.append("**Classified as an endpoint change:** `%s`" % path)
        md.append("")
        section("Backend handlers", eps, lambda e: "`{} {}` ({}.{}) in `{}`".format(
            e.get("method"), e.get("path"), e.get("controller"), e.get("action"), e.get("file")))
        section("Frontend callers", cross, lambda c: "`{}` (`{} {}`)".format(
            c.get("frontendFile"), c.get("method"), c.get("url")))
        section("Frontend files affected (reverse-import closure)",
                sorted(set(fe_seeds) | set(closure)), lambda x: "`%s`" % x)
        data.update({"handlers": eps, "frontendCallers": cross,
                     "frontendFilesAffected": sorted(set(fe_seeds) | set(closure))})

    else:
        md.append("Could not classify `%s` against the analyzed model." % changed)
        md.append("")
        md.append("Try an exact type name, a file path ending in `.cs`/`.ts`, "
                  "or an endpoint path starting with `/`.")
        data["error"] = "unclassified"

    # Always surface linker gaps + a verification checklist.
    md.append("## Linker gaps to review")
    md.append("- Unmatched frontend calls: **{}**".format(
        links.get("summary", {}).get("unmatchedFrontendCalls", 0)))
    md.append("- Unused/unlinked endpoints: **{}**".format(
        links.get("summary", {}).get("unusedEndpoints", 0)))
    md.append("")
    md.append("## Verify before you trust it")
    md.append("- [ ] Confirm the workspace contained *all* relevant repos (missing code = missing edges).")
    md.append("- [ ] Check for reflection / DI-by-convention / message-bus handlers the static pass can't see.")
    md.append("- [ ] Re-check any endpoint whose match confidence is `loose` or that used a `*` wildcard.")
    md.append("- [ ] Cross-check the affected set against the compiler and the test suite.")
    md.append("")
    return "\n".join(md), data


def main(argv=None):
    ap = argparse.ArgumentParser(description="Cross-stack impact analysis.")
    ap.add_argument("--frontend", required=True, help="Angular source directory.")
    ap.add_argument("--backend", required=True, help=".NET source directory.")
    ap.add_argument("--changed", required=True, help="Changed type, file, or endpoint.")
    ap.add_argument("--out", default="./.impact-out")
    ap.add_argument("--refresh", action="store_true", help="Force re-analysis.")
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args(argv)

    backend, frontend, links = ensure_models(
        args.frontend, args.backend, args.out, args.refresh, args.python)

    cls = classify(args.changed, backend, frontend)
    report_md, data = build_report(args.changed, cls, backend, frontend, links)

    out = Path(args.out)
    (out / "impact.md").write_text(report_md, encoding="utf-8")
    with open(out / "impact.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2 if args.pretty else None)

    print(report_md)
    print("\n(impact.md and impact.json written to %s)" % out, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
