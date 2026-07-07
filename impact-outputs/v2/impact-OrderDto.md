# Impact analysis: `OrderDto`

**Classified as a backend change.** Changed types: `OrderDto`

## Backend files affected (3)
- `Api/Controllers/OrdersController.cs`
- `Application/Orders/OrderDto.cs`
- `Application/Orders/OrderService.cs`

## Backend API endpoints affected (4)
- `GET /api/Orders` (OrdersController.GetAll)
- `GET /api/Orders/{id}` (OrdersController.GetById)
- `GET /api/Orders/by-customer/{customerId}` (OrdersController.GetByCustomer)
- `POST /api/Orders/create` (OrdersController.Create)

## Cross-stack call paths (2)
- `src/app/orders/order.service.ts` -> `GET /api/Orders` -> `OrdersController.GetAll` _(match: exact)_
- `src/app/orders/order.service.ts` -> `GET /api/Orders/{id}` -> `OrdersController.GetById` _(match: param)_

## Frontend files affected (reverse-import closure) (3)
- `src/app/orders/order-detail.component.ts`
- `src/app/orders/order-list.component.ts`
- `src/app/orders/order.service.ts`

## Linker gaps to review
- Unmatched frontend calls: **1**
- Unused/unlinked endpoints: **2**

## Verify before you trust it
- [ ] Confirm the workspace contained *all* relevant repos (missing code = missing edges).
- [ ] Check for reflection / DI-by-convention / message-bus handlers the static pass can't see.
- [ ] Re-check any endpoint whose match confidence is `loose` or that used a `*` wildcard.
- [ ] Cross-check the affected set against the compiler and the test suite.
