---
name: api-map
description: Full frontend-to-backend API map — every Angular HttpClient call mapped to its .NET controller/action.
agent: Impact Analyst
---

Produce the complete cross-stack API map for this workspace — an onboarding /
architecture artifact.

1. Locate the Angular and .NET source roots. Run the engine's analyzers + linker
   (same commands as `/unused-endpoints`), or reuse `./.impact-out` if it is fresh.
2. From `links.json` → `crossEdges`, build a table **grouped by controller**, with
   columns:
   - **Endpoint** (verb + path)
   - **Controller.Action**
   - **Calling Angular file(s)**
   - **Match confidence** (`exact` / `param` / `loose`)
3. Add a short summary line: number of endpoints, number linked, and **coverage**
   (% of endpoints with at least one frontend caller).
4. At the end, list any endpoints with **no** caller and any calls with **no**
   endpoint.

Make it scannable, and offer to save it as `api-map.md`.
