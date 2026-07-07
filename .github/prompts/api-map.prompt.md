---
name: api-map
description: Map Angular HTTP calls to .NET controller endpoints.
agent: Impact Analyst
argument-hint: '[scope=...]'
---

# API Map

## Inputs

* ${input:scope:auto}: (Optional, defaults to auto) App, release, environment, version, or `compare`.

## Requirements

1. Follow the `Impact Analyst` workspace and scope selection rules.
2. Build or reuse a fresh model for the selected scope-specific output folder.
3. From `links.json`, use `crossEdges` to build a table grouped by controller.
4. Include endpoint, controller action, calling Angular files, and match
   confidence in the table.
5. Add coverage using endpoint count and linked endpoint count.
6. List unused endpoints and unmatched frontend calls at the end.
7. Offer to save the result as `api-map-<scope>.md` when the user wants a file.
