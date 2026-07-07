---
name: pr-impact
description: Combined blast radius of your current uncommitted changes across both stacks — a PR-readiness view.
agent: Impact Analyst
argument-hint: (optional) a base branch/ref to diff against, e.g. origin/main
---

Analyse the impact of the **current working changes** in this workspace. If a base
ref is given in the chat input, diff against it; otherwise diff the uncommitted
working tree.

1. Use the #tool:changes tool (or `git diff --name-only`) to list the changed files.
2. Locate the Angular and .NET source roots. Run the engine once with `--refresh`
   to build the model, then reuse the cached model for the remaining items:
   ```
   python .github/skills/impact-analysis/scripts/impact_of_change.py \
     --frontend <angular-root> --backend <dotnet-root> \
     --changed "<changed file or symbol>" --out ./.impact-out
   ```
   Run it for each changed `.cs` type/file and each changed `.ts` file.
3. Merge into a single report: the de-duplicated union of **Backend affected** and
   **Frontend affected**, plus every **Cross-stack path** touched.
4. Put the **highest-risk items first** — anything touched by multiple changes, and
   any breaking DTO / endpoint change.
5. End with the "Verify before you trust it" checklist.

Write it so a reviewer can skim the blast radius in under a minute.
