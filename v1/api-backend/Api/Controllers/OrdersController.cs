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

    [HttpPost]
    public OrderDto Create(OrderDto dto) => _orders.Create(dto);
}
