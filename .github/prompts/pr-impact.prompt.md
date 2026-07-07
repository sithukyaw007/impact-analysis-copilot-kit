---
name: pr-impact
description: Analyze current working changes for cross-stack PR readiness.
agent: Impact Analyst
argument-hint: '[baseRef=origin/main] [scope=...]'
---

# PR Impact

## Inputs

* ${input:baseRef:working-tree}: (Optional, defaults to working-tree) Base branch or ref to diff against.
* ${input:scope:auto}: (Optional, defaults to auto) App, release, environment, version, or `compare`.

## Requirements

1. Use available changes tooling or `git diff --name-only` to list changed files.
   If the provided `baseRef` is not `working-tree`, diff against that ref.
   Otherwise use the uncommitted working tree.
2. Follow the `Impact Analyst` workspace and scope selection rules. If changes
   span multiple frontend/backend pairs, analyze each pair separately.
3. Run the impact-analysis engine for each relevant `.cs` type or file and each
   changed `.ts` file that participates in the selected pair.
4. Merge results into a single reviewer-friendly report with de-duplicated
   backend files, frontend files, and cross-stack paths.
5. Put the highest-risk items first, especially breaking DTO or endpoint changes
   and items touched by multiple changes.
6. End with the "Verify before you trust it" checklist.
