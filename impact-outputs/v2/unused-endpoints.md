# Integration-gap sweep — v2 (after change)

## Unused endpoints (2)
- `GET /api/Orders/by-customer/{customerId}` (OrdersController.GetByCustomer) — no frontend call hits this route (dead code, renamed, or consumed by another client).
- `POST /api/Orders/create` (OrdersController.Create) — no frontend call hits this route (dead code, renamed, or consumed by another client).

## Unmatched frontend calls (1)
- `POST /api/orders` in `src/app/orders/order.service.ts` — no backend route matches (broken/renamed endpoint, or external API).
