# Methodology, fidelity, and how to escalate

This engine trades a little completeness for **zero-install, read-only,
compile-free** analysis that runs anywhere. This note explains what it captures,
where it is approximate, and how to raise fidelity when a decision demands it.

## What each layer captures

| Layer | Source of truth | Confidence |
|-------|-----------------|-----------|
| .NET project graph | `*.csproj` `ProjectReference` / `PackageReference` | **High** — declarative, exact |
| .NET API endpoints | `[Route]` + `[HttpGet/Post/...]` attributes on controllers | **High** for attribute-routed APIs |
| .NET DI edges | constructor parameter types | **Medium** — misses property/factory injection |
| .NET type references | word-boundary name matches across `.cs` files | **Medium** — can over/under-count |
| Angular import graph | `import ... from './...'` relative resolution | **High** for static imports |
| Angular HTTP calls | `HttpClient` `.get/.post/...` string/template URLs | **Medium** — literal/template portions only |
| Cross-stack links | verb + path-template match of calls to routes | **Medium** — see below |

## Known blind spots

- **Runtime wiring**: reflection, DI-by-convention, dynamically registered routes, MediatR / message-bus handlers, and minimal APIs registered in `Program.cs` via `app.MapGet(...)` (only attribute-routed controllers are parsed today).
- **Composed URLs**: frontend URLs assembled by string concatenation or read from runtime config — only the literal and `${...}` template parts are normalized to wildcards.
- **Base-path mismatches**: if the frontend prepends a base URL injected at runtime, matches fall back to `loose` confidence.
- **Type-reference noise**: common type names can match unrelated files; treat the `typeReferences` set as a *candidate* list, not proof.

Because of these, the tool is authoritative for **"where to look"** and a strong
first pass for **"what's affected"**, but its output should be **verified**
against the compiler and tests before any high-stakes change.

## Raising fidelity (optional add-ons)

### Backend → compiler-accurate
- **`dotnet build -graph -bl`** then inspect the binary log, or use the **MSBuild static graph** to get an exact project graph.
- **Roslyn** (`Microsoft.CodeAnalysis`): load the solution with `MSBuildWorkspace`, then use `SymbolFinder.FindReferencesAsync` for exact symbol references and `FindCallersAsync` for call graphs. This replaces the heuristic `typeReferences` and `diEdges` with ground truth. Swap the output of `analyze_dotnet.py` for a Roslyn tool that emits the same JSON shape and the rest of the pipeline is unchanged.
- **Minimal APIs / endpoint metadata**: at runtime, `EndpointDataSource` enumerates every registered route; a tiny diagnostic endpoint can dump the real route table to compare against the static one.

### Frontend → richer graph
- **`npx madge --json src/`** for a complete module dependency graph (handles path aliases and barrels better than the relative-only resolver here).
- **Angular compiler / `ng` build stats** or **ts-morph** for decorator-aware component/service/provider graphs.
- **OpenAPI**: generate a client from the .NET API's Swagger doc; matching frontend calls to generated client methods is far more reliable than URL-string matching.

## Keeping the JSON contract stable

The four scripts communicate through a fixed JSON shape (`backend.json`,
`frontend.json`, `links.json`). Any higher-fidelity replacement only has to emit
the same fields — `endpoints`, `types`, `diEdges`, `typeReferences`,
`importEdges`, `httpCalls`, `crossEdges` — so you can upgrade one stage at a time
without touching `impact_of_change.py`.
