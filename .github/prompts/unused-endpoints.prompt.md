---
name: unused-endpoints
description: Sweep for dead API routes and frontend calls that have no matching backend route.
agent: Impact Analyst
---

Do an integration-gap sweep across the Angular + .NET stacks.

1. Locate the Angular and .NET source roots.
2. Build the model and links:
   ```
   python .github/skills/impact-analysis/scripts/analyze_dotnet.py  --root <dotnet-root>  --out ./.impact-out/backend.json
   python .github/skills/impact-analysis/scripts/analyze_angular.py --root <angular-root> --out ./.impact-out/frontend.json
   python .github/skills/impact-analysis/scripts/link_cross_stack.py \
     --backend ./.impact-out/backend.json --frontend ./.impact-out/frontend.json \
     --out ./.impact-out/links.json
   ```
3. From `links.json`, report two tables:
   - **Unused endpoints** — backend routes no frontend call appears to hit
     (candidate dead code, or consumed by another client / service).
   - **Unmatched frontend calls** — HTTP calls with no matching backend route
     (broken or renamed endpoints, or genuinely external APIs).
4. For each item, note the **likely cause** and a **suggested next check**.

Remind the reader these are heuristic: a `loose` matcher can miss routes that the
frontend reaches through a runtime-injected base path, so confirm before deleting
anything.
