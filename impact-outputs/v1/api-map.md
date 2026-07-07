# API map — v1 (baseline)

**Coverage:** 5/5 endpoints have at least one frontend caller (100%).

| Endpoint | Controller.Action | Calling Angular file | Confidence |
|---|---|---|---|
| `GET /api/Customers/{id}` | CustomersController.GetById | `src/app/customers/customer.service.ts` | param |
| `POST /api/Customers` | CustomersController.Create | `src/app/customers/customer.service.ts` | exact |
| `GET /api/Orders` | OrdersController.GetAll | `src/app/orders/order.service.ts` | exact |
| `GET /api/Orders/{id}` | OrdersController.GetById | `src/app/orders/order.service.ts` | param |
| `POST /api/Orders` | OrdersController.Create | `src/app/orders/order.service.ts` | exact |
