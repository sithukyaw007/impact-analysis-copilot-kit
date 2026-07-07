---
title: Change Set from v1 to v2
description: Reference change log for the intentional Angular and .NET updates used by the impact-analysis sample.
author: Microsoft
ms.date: 2026-07-07
ms.topic: reference
keywords:
  - impact analysis
  - changelog
  - angular
  - dotnet
estimated_reading_time: 3
---

## Purpose

Keep this file as the scenario contract for the worked example. The main
`README.md` summarizes what the engine found, while this file explains the exact
v1 to v2 changes that produced those findings.

The change set deliberately spans the frontend and backend boundary and leaves
one loose end. That makes it useful for validating whether the impact-analysis
engine can identify contract changes, route moves, unmatched frontend calls, and
unused backend endpoints.

## Backend changes

| File                                  | Change                                                                 | Type                     |
|---------------------------------------|------------------------------------------------------------------------|--------------------------|
| `Application/Orders/OrderDto.cs`      | Renamed `Total` to `TotalAmount`; added `Currency`.                    | Breaking shared contract |
| `Api/Controllers/OrdersController.cs` | Moved create route to `POST /api/orders/create`.                       | Breaking route           |
| `Api/Controllers/OrdersController.cs` | Added `GET /api/orders/by-customer/{customerId}`.                      | New feature              |
| `Application/Orders/OrderService.cs`  | Added `GetByCustomer(...)`; `Get(...)` now sets amount and currency.   | Supporting change        |

## Frontend changes

| File                      | Change                                                                  | Type                    |
|---------------------------|-------------------------------------------------------------------------|-------------------------|
| `orders/order.model.ts`   | Renamed `total` to `totalAmount`; added `currency`.                     | Reconciled with backend |
| `orders/order.service.ts` | Left unchanged on purpose and still calls `POST /api/orders`.           | Intentional loose end   |

## Expected analysis findings

1. The `OrderDto` blast radius should include `OrderDto`, `OrderService`, and
   `OrdersController` on the backend, plus `order.service.ts` and its
   `order-list` and `order-detail` importers on the frontend.
2. The integration-gap sweep should report one unmatched frontend call because
   the frontend still posts to `POST /api/orders`.
3. The endpoint sweep should report two unused endpoints:
   `POST /api/orders/create` and `GET /api/orders/by-customer/{customerId}`.
4. The API map coverage should fall from 100 percent in v1 to 67 percent in v2.

## Related generated outputs

The generated reports under `impact-outputs/` show these expected findings:

* `impact-outputs/v2/impact-OrderDto.md`
* `impact-outputs/v2/api-map.md`
* `impact-outputs/v2/unused-endpoints.md`
* `impact-outputs/v2/links.json`
