---
description: Example prompts and command output shapes for the impact-analysis skill.
---

# Sample usage

These examples assume a multi-root workspace containing an Angular app under
`./web` and a .NET solution under `./api`.

## 1. "What breaks if I change the CustomerDto?"

Prompt to Copilot (agent mode, with this skill installed):

> Use the impact-analysis skill: what's affected if I change `CustomerDto`?

What the skill runs under the hood:

```bash
python scripts/impact_of_change.py --frontend ./web --backend ./api \
       --changed "CustomerDto" --out ./.impact-out/current
```

Shape of the report (`impact.md`):

```text
# Impact analysis: `CustomerDto`
**Classified as a backend change.** Changed types: `CustomerDto`

## Backend files affected (4)
- `api/Application/Customers/CustomerService.cs`
- `api/Api/Controllers/CustomersController.cs`
- ...

## Backend API endpoints affected (3)
- `GET /api/customers/{id}` (CustomersController.GetById)
- `POST /api/customers` (CustomersController.Create)
- ...

## Cross-stack call paths (2)
- `web/src/app/customers/customer.service.ts` -> `GET /api/customers/{id}`
  -> `CustomersController.GetById` _(match: param)_

## Frontend files affected (reverse-import closure) (5)
- `web/src/app/customers/customer.service.ts`
- `web/src/app/customers/customer-detail/customer-detail.component.ts`
- ...

## Linker gaps to review
- Unmatched frontend calls: 1
- Unused/unlinked endpoints: 2
```

## 2. "Which frontend code depends on this Angular service?"

> Impact of changing `order.service.ts`?

```bash
python scripts/impact_of_change.py --frontend ./web --backend ./api \
       --changed "src/app/orders/order.service.ts" --out ./.impact-out/current
```

Returns the reverse-import closure (every component/module that transitively
imports the service) plus the backend endpoints that service calls.

## 3. "Who consumes this endpoint?"

> Who calls `/api/orders/{id}`?

```bash
python scripts/impact_of_change.py --frontend ./web --backend ./api \
       --changed "/api/orders/{id}" --out ./.impact-out/current
```

Returns the backend handler(s) plus every frontend caller and its import closure.

## 4. Just build/refresh the model

```bash
python scripts/analyze_dotnet.py  --root ./api --out ./.impact-out/current/backend.json  --pretty
python scripts/analyze_angular.py --root ./web --out ./.impact-out/current/frontend.json --pretty
python scripts/link_cross_stack.py --backend ./.impact-out/current/backend.json \
       --frontend ./.impact-out/current/frontend.json --out ./.impact-out/current/links.json --pretty
```

Inspect `links.json` for `unmatchedFrontendCalls` and `unusedEndpoints`, the
highest-signal findings (integration gaps and dead routes).

> Tip: add `--refresh` to `impact_of_change.py` to force a rebuild after code changes.
