---
name: impact-analysis
description: >-
  Cross-repository impact-analysis engine for an application with an Angular
  frontend and a .NET (Core) backend. Use this skill when asked to trace
  dependencies, find affected components, map frontend-to-backend API
  relationships, or answer "what breaks if I change X?" across the Angular and
  .NET code in the workspace. Triggers: impact analysis, dependency graph,
  affected components, blast radius, cross-repository / cross-stack analysis,
  which controller does this call hit, who consumes this endpoint / DTO.
---

# Angular ↔ .NET Impact-Analysis Engine

This skill turns Copilot from *guessing* about dependencies into *reporting* on
them. It runs deterministic static-analysis scripts over the Angular frontend
and the .NET (Core) backend, builds a real dependency model, links the two
stacks by matching HTTP calls to API routes, and then computes the blast radius
of a proposed change. Copilot's job is to **orchestrate the scripts and explain
the results in business terms** — not to infer the relationships itself.

## When to use this skill

Use it whenever the request is about relationships *between* pieces of code,
especially across the frontend/backend boundary:

- "What breaks if I change the `CustomerDto` / `GET /api/orders/{id}` / this Angular service?"
- "Which Angular components call this .NET endpoint?"
- "Map the frontend calls to backend controllers."
- "Show the dependency graph / affected components for this change."
- "Which endpoints are unused? Which frontend calls have no matching backend route?"

Do **not** use it for single-file questions, code authoring, or formatting —
those don't need the dependency model.

## Prerequisites

- **Python 3.8+** on PATH (the analyzers use only the standard library — no `pip install` required).
- A **multi-root VS Code workspace** that contains *both* the Angular frontend and the .NET backend, so all relevant code is on disk. Cross-stack linking is only as complete as the code the workspace can see.
- Optional, for higher fidelity (see [methodology](./references/methodology.md)):
  - Node.js + `npx madge` for a richer Angular import graph.
  - .NET SDK for a compiler-accurate backend graph via Roslyn / `dotnet build -graph`.

## How it works

Four scripts under [`scripts/`](./scripts), run in sequence. Each writes JSON so
results are inspectable and cacheable:

| Step | Script | Produces |
|------|--------|----------|
| 1 | [`analyze_dotnet.py`](./scripts/analyze_dotnet.py) | Projects, project/package references, API endpoints (controller + action routes + verbs), defined types, DI edges, type references → `backend.json` |
| 2 | [`analyze_angular.py`](./scripts/analyze_angular.py) | Components/services/modules, import graph, and every `HttpClient` call with its URL → `frontend.json` |
| 3 | [`link_cross_stack.py`](./scripts/link_cross_stack.py) | Frontend HTTP call ↔ backend route matches, plus unmatched calls and unused endpoints → `links.json` |
| 4 | [`impact_of_change.py`](./scripts/impact_of_change.py) | Given a changed file / type / endpoint, the downstream affected components across **both** stacks → `impact.md` + `impact.json` |

`impact_of_change.py` is the entry point for most questions — it runs steps 1–3
automatically if the JSON artifacts aren't already present.

## Usage

Run everything with one command (from the skill's `scripts/` folder):

```bash
python impact_of_change.py \
  --frontend <path-to-angular-src> \
  --backend  <path-to-dotnet-src> \
  --changed  "CustomerDto" \
  --out      ./.impact-out
```

`--changed` accepts any of:
- a **type/class name** (e.g. `CustomerDto`, `OrdersController`),
- a **file path** (e.g. `src/app/orders/order.service.ts` or `Api/Controllers/OrdersController.cs`),
- an **endpoint path** (e.g. `/api/orders/{id}`).

To (re)generate just the model without an impact query:

```bash
python analyze_dotnet.py  --root <backend-src>  --out ./.impact-out/backend.json
python analyze_angular.py --root <frontend-src> --out ./.impact-out/frontend.json
python link_cross_stack.py --backend ./.impact-out/backend.json \
       --frontend ./.impact-out/frontend.json --out ./.impact-out/links.json
```

## What to do with the output (instructions for the agent)

1. Run `impact_of_change.py` with the changed symbol/file the user named.
2. Read `impact.json` and summarise **in business terms**, grouped as:
   - **Backend affected** — controllers, services, DTOs, projects.
   - **Frontend affected** — services, components, modules (including the reverse-import closure).
   - **Cross-stack path** — the exact call → route → controller chain that links them.
3. Always surface the linker's **`unmatchedFrontendCalls`** and **`unusedEndpoints`** — they reveal gaps the heuristics couldn't resolve and are often the most useful findings.
4. Present a short **"verify before you trust it"** checklist (see fidelity notes) — this is heuristic static analysis, not a compiler.

## Fidelity & limitations (read before relying on results)

This engine is **compile-free and heuristic**. It is excellent for *locating*
relationships and scoping a change, but it is not a guaranteed-complete graph.
It can miss:

- Runtime-only wiring: reflection, dependency injection resolved by convention, dynamic route registration, MediatR/message-bus handlers.
- HTTP URLs built by string concatenation or resolved from config at runtime (only literal/template portions are captured).
- Cross-stack links where the frontend base URL is injected at runtime.

**Always verify** high-stakes conclusions against the compiler, the app's tests,
and a quick search. For production-grade fidelity, escalate the backend to a
Roslyn analyzer or `dotnet build -graph`, and the frontend to `madge` — see
[references/methodology.md](./references/methodology.md).

## Governance notes (for regulated / enterprise use)

- The scripts perform **read-only static analysis**. They parse source text and emit JSON; they do **not** build, execute, or modify the target application.
- No network calls and no third-party packages — standard library only — so they are safe to run in locked-down or air-gapped environments.
- Review and pin the scripts before adding them to a shared repository, and treat any future high-fidelity add-ons (Roslyn packages, `madge`) as normal supply-chain dependencies.

## Examples

See [examples/sample-usage.md](./examples/sample-usage.md) for concrete prompts
and the shape of the reports they produce.
