---
name: impact
description: Blast radius of changing a type, file, or endpoint across the Angular + .NET stacks.
agent: Impact Analyst
argument-hint: a type, file, or endpoint (e.g. CustomerDto, order.service.ts, /api/orders/{id})
---

Run a cross-stack impact analysis for: **${input:changed:the type, file, or endpoint that changed}**

1. Locate the Angular source root and the .NET source root in this workspace.
2. Run the impact-analysis engine:
   ```
   python .github/skills/impact-analysis/scripts/impact_of_change.py \
     --frontend <angular-root> --backend <dotnet-root> \
     --changed "${input:changed}" --out ./.impact-out --refresh
   ```
3. Read `./.impact-out/impact.json` and report, grouped as:
   - **Backend affected** — controllers, services, DTOs, projects.
   - **Frontend affected** — services, components, modules (reverse-import closure).
   - **Cross-stack path** — the call → route → controller chain that links them.
4. Surface `unmatchedFrontendCalls` and `unusedEndpoints`, then end with the
   "Verify before you trust it" checklist.

Keep it concise, quote exact file paths and routes, and flag any `loose` or
wildcard (`*`) matches as lower-confidence.
