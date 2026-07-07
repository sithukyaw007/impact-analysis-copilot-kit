---
name: unused-endpoints
description: Sweep for dead API routes and frontend calls that have no matching backend route.
agent: Impact Analyst
argument-hint: '[scope=...]'
---

# Unused Endpoints

## Inputs

* ${input:scope:auto}: (Optional, defaults to auto) App, release, environment, version, or `compare`.

## Requirements

1. Follow the `Impact Analyst` workspace and scope selection rules.
2. Build or reuse a fresh model and link graph for the selected scope-specific
  output folder.
3. Report unused backend endpoints that no frontend call appears to hit.
4. Report unmatched frontend calls that have no matching backend route.
5. For each item, include the likely cause and a suggested next check.
6. Remind the reader that static matching is heuristic and that runtime base
  paths, external clients, or generated clients can change the conclusion.
