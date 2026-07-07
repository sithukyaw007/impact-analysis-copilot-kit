using Application.Customers;

namespace Application.Orders;

public interface IOrderService
{
    IEnumerable<OrderDto> GetAll();
    OrderDto Get(int id);
    OrderDto Create(OrderDto dto);
}

public class OrderService : IOrderService
{
    private readonly ICustomerService _customers;

    public OrderService(ICustomerService customers)
    {
        _customers = customers;
    }

    public IEnumerable<OrderDto> GetAll() => new List<OrderDto>();

    public OrderDto Get(int id) => new OrderDto { Id = id, CustomerId = 1, Total = 0m };

    public OrderDto Create(OrderDto dto) => dto;
}
