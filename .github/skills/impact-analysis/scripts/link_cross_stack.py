#!/usr/bin/env python3
"""
link_cross_stack.py - links an Angular frontend model to a .NET backend model by
matching HTTP calls to API routes. Produces:

  - crossEdges: frontend call -> backend endpoint (controller/action/file)
  - unmatchedFrontendCalls: calls with no matching route (gaps / external APIs)
  - unusedEndpoints: routes no frontend call appears to hit (dead code / other clients)

Matching is verb + path-template aware: a backend `{id}` route parameter and a
frontend `*` (from `${...}` or numeric/guid segments) are treated as wildcards.

Usage:
  python link_cross_stack.py --backend backend.json --frontend frontend.json
         --out links.json [--pretty]
"""
import argparse
import json
import re
import sys
from pathlib import Path


def endpoint_segments(path):
    """Backend route -> list of segments, with route params ({id}) as '*'."""
    segs = []
    for seg in path.split("/"):
        if seg == "":
            continue
        if seg.startswith("{") and seg.endswith("}"):
            segs.append("*")
        elif seg.startswith("[") and seg.endswith("]"):
            segs.append("*")  # unresolved token
        else:
            # a param embedded like "orders{id}" -> keep literal prefix lowered
            segs.append(re.sub(r'\{[^}]*\}', "", seg).lower())
    return segs


def url_segments(url):
    segs = []
    for seg in url.split("/"):
        if seg == "":
            continue
        segs.append(seg)  # already normalized/lowered by analyzer
    return segs


def seg_match(ep_segs, url_segs):
    """True if the url segments satisfy the endpoint template."""
    if len(ep_segs) != len(url_segs):
        return False, "none"
    used_wildcard = False
    for e, u in zip(ep_segs, url_segs):
        if e == "*" or u == "*":
            used_wildcard = used_wildcard or True
            continue
        if e != u:
            return False, "none"
    return True, ("param" if used_wildcard else "exact")


def loose_tail_match(ep_segs, url_segs):
    """Fallback: the url ends with the endpoint's static tail (base-path differences)."""
    ep_static = [s for s in ep_segs if s != "*"]
    if not ep_static:
        return False
    joined = "/".join(url_segs)
    return "/".join(ep_static) in joined


def main(argv=None):
    ap = argparse.ArgumentParser(description="Link Angular calls to .NET routes.")
    ap.add_argument("--backend", required=True)
    ap.add_argument("--frontend", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args(argv)

    backend = json.loads(Path(args.backend).read_text(encoding="utf-8"))
    frontend = json.loads(Path(args.frontend).read_text(encoding="utf-8"))

    endpoints = backend.get("endpoints", [])
    ep_index = []
    for ep in endpoints:
        ep_index.append({
            "ep": ep,
            "segs": endpoint_segments(ep.get("path", "")),
            "method": (ep.get("method") or "").upper(),
        })

    cross_edges = []
    unmatched = []
    matched_ep_ids = set()

    for call in frontend.get("httpCalls", []):
        u_segs = url_segments(call.get("url", ""))
        method = (call.get("method") or "").upper()
        best = None
        for idx, e in enumerate(ep_index):
            if e["method"] != method:
                continue
            ok, conf = seg_match(e["segs"], u_segs)
            if ok:
                best = (idx, conf)
                if conf == "exact":
                    break
        if best is None:
            # loose fallback (verb match + static tail contained)
            for idx, e in enumerate(ep_index):
                if e["method"] != method:
                    continue
                if loose_tail_match(e["segs"], u_segs):
                    best = (idx, "loose")
                    break
        if best is None:
            unmatched.append(call)
            continue
        idx, conf = best
        ep = ep_index[idx]["ep"]
        matched_ep_ids.add(idx)
        cross_edges.append({
            "frontendFile": call.get("file"),
            "method": method,
            "url": call.get("url"),
            "rawUrl": call.get("rawUrl"),
            "endpointPath": ep.get("path"),
            "controller": ep.get("controller"),
            "action": ep.get("action"),
            "backendFile": ep.get("file"),
            "confidence": conf,
        })

    unused = [ep_index[i]["ep"] for i in range(len(ep_index)) if i not in matched_ep_ids]

    result = {
        "crossEdges": cross_edges,
        "unmatchedFrontendCalls": unmatched,
        "unusedEndpoints": unused,
        "summary": {
            "crossEdges": len(cross_edges),
            "unmatchedFrontendCalls": len(unmatched),
            "unusedEndpoints": len(unused),
        },
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2 if args.pretty else None)
    s = result["summary"]
    print("links: {crossEdges} matched, {unmatchedFrontendCalls} unmatched calls, "
          "{unusedEndpoints} unused endpoints -> {out}".format(out=args.out, **s),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
