# API map — v2 (after change)

**Coverage:** 4/6 endpoints have at least one frontend caller (67%).

| Endpoint | Controller.Action | Calling Angular file | Confidence |
|---|---|---|---|
| `GET /api/Customers/{id}` | CustomersController.GetById | `src/app/customers/customer.service.ts` | param |
| `POST /api/Customers` | CustomersController.Create | `src/app/customers/customer.service.ts` | exact |
| `GET /api/Orders` | OrdersController.GetAll | `src/app/orders/order.service.ts` | exact |
| `GET /api/Orders/{id}` | OrdersController.GetById | `src/app/orders/order.service.ts` | param |

**Endpoints with no frontend caller:**
- `GET /api/Orders/by-customer/{customerId}` (OrdersController.GetByCustomer)
- `POST /api/Orders/create` (OrdersController.Create)

**Frontend calls with no matching endpoint:**
- `POST /api/orders` (`src/app/orders/order.service.ts`)
