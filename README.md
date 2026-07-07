---
title: Impact Analysis Copilot Kit
description: Worked Angular and .NET impact-analysis example with GitHub Copilot skills, agents, prompts, and generated outputs.
author: Microsoft
ms.date: 2026-07-07
ms.topic: overview
keywords:
  - github copilot
  - impact analysis
  - angular
  - dotnet
  - static analysis
estimated_reading_time: 8
---

## Overview

Use this repository as both a worked example and a reusable GitHub Copilot kit for
cross-stack impact analysis. It contains two versions of a small Orders /
Customers application, generated impact-analysis outputs, and the Copilot
customizations that produce those outputs.

The generated files in `impact-outputs/` come from the engine in
`.github/skills/impact-analysis/scripts`. They are not speculative notes. They are
the result of static analysis across an Angular frontend and a .NET backend.

The kit helps answer questions such as:

* What breaks if I change `CustomerDto`, `OrderDto`, or an API endpoint?
* Which Angular services and components call a .NET controller route?
* Which backend endpoints appear unused by the frontend?
* Which frontend HTTP calls have no matching backend route?
* What is the blast radius of my current change set?

## How the kit is organized

The repository combines three Copilot customization layers with sample
applications and generated evidence.

| Layer        | Location                              | Role                                                                    |
|--------------|---------------------------------------|-------------------------------------------------------------------------|
| Skill        | `.github/skills/impact-analysis`      | Runs deterministic static analysis and writes JSON or Markdown outputs. |
| Custom agent | `.github/agents`                      | Provides focused Copilot entry points for analysis and migration plans. |
| Prompt files | `.github/prompts`                     | Adds slash-command shortcuts for common analysis workflows.             |
| Sample apps  | `v1/` and `v2/`                       | Provide Angular and .NET code for repeatable demonstrations.            |
| Outputs      | `impact-outputs/`                     | Stores generated reports from the engine.                               |

The `Impact Analyst` agent is read-only. It runs the analysis scripts, reads the
generated JSON, and explains the affected backend files, frontend files, and
frontend-to-backend links. The `Migration Planner` agent turns an impact report
into an ordered refactor checklist when you want a follow-up plan.

## Repository layout

```text
impact-analysis-copilot-kit/
|-- README.md
|-- CHANGELOG-v1-to-v2.md
|-- impact-analysis.code-workspace
|-- .github/
|   |-- agents/
|   |   |-- impact-analyst.agent.md
|   |   `-- migration-planner.agent.md
|   |-- prompts/
|   |   |-- api-map.prompt.md
|   |   |-- impact.prompt.md
|   |   |-- pr-impact.prompt.md
|   |   `-- unused-endpoints.prompt.md
|   `-- skills/
|       `-- impact-analysis/
|           |-- SKILL.md
|           |-- scripts/
|           |   |-- analyze_angular.py
|           |   |-- analyze_dotnet.py
|           |   |-- impact_of_change.py
|           |   `-- link_cross_stack.py
|           |-- examples/
|           `-- references/
|-- v1/
|   |-- api-backend/
|   `-- web-frontend/
|-- v2/
|   |-- api-backend/
|   `-- web-frontend/
`-- impact-outputs/
    |-- v1/
    `-- v2/
```

## Worked example scenario

The sample app has an Angular frontend and a .NET backend for Orders and
Customers.

* Version 1 is a working baseline where every frontend HTTP call maps to a
  backend route.
* Version 2 applies one round of changes: a shared DTO is refactored, an endpoint
  is moved, a new endpoint is added, and the frontend is mostly updated.

See [CHANGELOG-v1-to-v2.md](./CHANGELOG-v1-to-v2.md) for the exact v1 to v2
change set.

## What the engine found

| Output                | v1 baseline           | v2 after change                                |
|-----------------------|-----------------------|------------------------------------------------|
| `/impact OrderDto`    | Not applicable        | 3 backend files, 3 frontend files, 4 endpoints |
| `/api-map` coverage   | 100 percent, 5 of 5   | 67 percent, 4 of 6                             |
| `/unused-endpoints`   | 0 unused, 0 unmatched | 2 unused endpoints, 1 unmatched frontend call  |

The v2 sweep pinpoints the loose end automatically. The frontend still calls
`POST /api/orders`, which is unmatched and likely returns 404. Meanwhile,
`POST /api/orders/create` and `GET /api/orders/by-customer/{customerId}` are
unused from the frontend perspective.

> [!NOTE]
> Endpoint paths can render with controller-name casing, such as `/api/Orders`.
> The cross-stack linker matches case-insensitively, so frontend `/api/orders`
> still links correctly.

## Static-analysis pipeline

The skill uses four standard-library Python scripts. The scripts are layout
agnostic because they accept explicit frontend and backend paths.

| Step | Script                | Output                                                                 |
|------|-----------------------|------------------------------------------------------------------------|
| 1    | `analyze_dotnet.py`   | Projects, references, controllers, endpoints, DTOs, and type usages.   |
| 2    | `analyze_angular.py`  | Services, components, imports, and `HttpClient` calls.                 |
| 3    | `link_cross_stack.py` | Frontend HTTP calls matched to backend routes, plus integration gaps.  |
| 4    | `impact_of_change.py` | Blast-radius report for a changed type, file, or endpoint.             |

## Prerequisites

* VS Code with GitHub Copilot and agent mode enabled.
* Python 3.8 or later on `PATH`.
* A multi-root workspace that contains the Angular frontend and .NET backend.
* Optional Node.js and .NET SDK tooling if you want to add higher-fidelity import
  or compiler-based analysis later.

The included scripts use only the Python standard library. You do not need to run
`pip install` for the default engine.

## Open the VS Code workspace

Open `impact-analysis.code-workspace` with **File > Open Workspace from File...**.
The workspace is configured for this repository and loads these folders:

* `v1/web-frontend`
* `v1/api-backend`
* `v2/web-frontend`
* `v2/api-backend`
* `impact-outputs`
* `.github`

The workspace also points Copilot at the kit customizations:

```jsonc
"settings": {
  "chat.agentSkillsLocations": { ".github/skills/**": true },
  "chat.promptFilesLocations": { ".github/prompts/**": true },
  "chat.agentFilesLocations":  { ".github/agents/**": true },
  "chat.useCustomizationsInParentRepositories": true
}
```

Reload the VS Code window after opening the workspace. In Copilot Chat, check
`/agents` and `/prompts` to confirm the `Impact Analyst`, `Migration Planner`,
`/impact`, `/api-map`, `/pr-impact`, and `/unused-endpoints` customizations are
available.

## Reproduce the sample outputs

Run the scripts from the repository root.

```bash
SCRIPTS=.github/skills/impact-analysis/scripts

# Blast radius of the OrderDto change in v2.
python3 "$SCRIPTS/impact_of_change.py" \
  --frontend v2/web-frontend --backend v2/api-backend \
  --changed "OrderDto" --out ./.out-v2 --refresh

# Integration-gap sweep for v2.
python3 "$SCRIPTS/analyze_dotnet.py" \
  --root v2/api-backend \
  --out ./.out-v2/backend.json

python3 "$SCRIPTS/analyze_angular.py" \
  --root v2/web-frontend \
  --out ./.out-v2/frontend.json

python3 "$SCRIPTS/link_cross_stack.py" \
  --backend ./.out-v2/backend.json \
  --frontend ./.out-v2/frontend.json \
  --out ./.out-v2/links.json \
  --pretty
```

Inspect `./.out-v2/links.json` for `crossEdges`, `unusedEndpoints`, and
`unmatchedFrontendCalls`.

## Use Copilot shortcuts

After the workspace loads and Copilot discovers the customizations, select the
`Impact Analyst` agent in Copilot Chat.

* Use `/impact OrderDto` to scope the blast radius of the `OrderDto` change.
* Use `/api-map` to generate the frontend-to-backend route map.
* Use `/unused-endpoints` to find dead backend routes and unmatched frontend
  calls.
* Use `/pr-impact` to analyze the current uncommitted change set.

For an interactive request, ask the `Impact Analyst` agent a question such as
"What breaks if I change `CustomerDto`?" or "Which frontend components call
`GET /api/orders/{id}`?"

## Use the kit in another codebase

For a real application, load the Angular and .NET repositories into one VS Code
multi-root workspace. Then place the `.github` customizations where Copilot can
discover them.

### Dedicated tooling folder

Keep one version-controlled folder, such as `dev-tooling`, that contains
`.github/skills`, `.github/agents`, and `.github/prompts`. Add that folder to the
multi-root workspace beside the app repositories, then point the workspace
settings at the tooling folder.

### User profile installation

Install the kit under your user profile, such as `~/.copilot/skills`,
`~/.copilot/agents`, and `~/.copilot/prompts`. This makes the customizations
available across workspaces, but the setup is personal rather than shared through
the repository.

### Per-folder customizations

Copy the `.github` content into a repository that participates in the workspace.
This is convenient for small setups, but it can duplicate the kit across multiple
repositories.

Copilot indexes the loaded multi-root workspace. For larger estates, use
**Build local workspace index** from the Command Palette when you need broader
local indexing.

## Tenant-specific checks

Two values can vary by organization:

* The `model` entries in `.github/agents/*.agent.md` are ordered preferences. Edit
  them to models enabled in your Copilot tenant if the listed models are not
  available.
* The `agent` values in handoffs may need the display name, such as
  `Impact Analyst`, or the file-name stem, such as `impact-analyst`, depending on
  tenant behavior.

## Fidelity and governance

The engine is compile-free and heuristic. It is excellent for locating likely
relationships and scoping change impact, but it is not a substitute for builds,
tests, or compiler-backed analysis.

Known limitations include:

* Runtime-only wiring through reflection, convention-based dependency injection,
  or dynamically registered routes.
* Message-bus handlers, background jobs, or integration points outside HTTP
  controller routes.
* URLs assembled entirely at runtime from configuration or string operations.
* Cross-stack links where the frontend base URL is injected at runtime.

The default scripts are read-only. They parse source text, emit JSON, make no
network calls, and require no third-party packages. For higher fidelity, you can
extend the backend side with Roslyn or `dotnet build -graph`, and the frontend
side with tools such as `madge`. The JSON contracts are intentionally stable so
you can upgrade one stage without rewriting the rest of the workflow.
