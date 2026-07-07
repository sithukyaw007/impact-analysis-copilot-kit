using Application.Customers;

namespace Application.Orders;

public interface IOrderService
{
    IEnumerable<OrderDto> GetAll();
    OrderDto Get(int id);
    IEnumerable<OrderDto> GetByCustomer(int customerId);   // v2: new
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

    public OrderDto Get(int id) =>
        new OrderDto { Id = id, CustomerId = 1, TotalAmount = 0m, Currency = "SGD" };

    // v2: new query used by the new by-customer endpoint.
    public IEnumerable<OrderDto> GetByCustomer(int customerId) => new List<OrderDto>();

    public OrderDto Create(OrderDto dto) => dto;
}
