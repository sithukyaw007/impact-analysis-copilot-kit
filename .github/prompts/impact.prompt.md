---
name: impact
description: Analyze blast radius for a type, file, or endpoint across Angular and .NET.
agent: Impact Analyst
argument-hint: changed=... [scope=...]
---

# Impact

## Inputs

* ${input:changed}: (Required) Type, file, or endpoint to analyze.
* ${input:scope:auto}: (Optional, defaults to auto) App, release, environment, version, or `compare`.

## Requirements

1. Analyze `${input:changed}` by following the `Impact Analyst` workspace and scope selection rules.
2. Run the impact-analysis engine for the selected frontend/backend pair, or for
   each pair when the request is a comparison.
3. Use scope-specific output folders so cached artifacts from different pairs do
   not collide.
4. Report the analyzed scope, affected backend files, affected frontend files,
   cross-stack paths, unmatched frontend calls, and unused endpoints.
5. Flag `loose` or wildcard (`*`) matches as lower confidence, then end with the
   "Verify before you trust it" checklist.
