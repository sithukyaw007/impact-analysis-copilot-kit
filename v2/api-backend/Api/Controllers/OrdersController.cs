using Application.Orders;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class OrdersController : ControllerBase
{
    private readonly IOrderService _orders;

    public OrdersController(IOrderService orders)
    {
        _orders = orders;
    }

    [HttpGet]
    public IEnumerable<OrderDto> GetAll() => _orders.GetAll();

    [HttpGet("{id}")]
    public OrderDto GetById(int id) => _orders.Get(id);

    // v2: new endpoint.
    [HttpGet("by-customer/{customerId}")]
    public IEnumerable<OrderDto> GetByCustomer(int customerId) => _orders.GetByCustomer(customerId);

    // v2: create route moved from POST /api/orders to POST /api/orders/create.
    [HttpPost("create")]
    public OrderDto Create(OrderDto dto) => _orders.Create(dto);
}
