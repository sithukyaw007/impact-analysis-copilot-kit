namespace Application.Customers;

public interface ICustomerService
{
    CustomerDto Get(int id);
    CustomerDto Create(CustomerDto dto);
}

public class CustomerService : ICustomerService
{
    public CustomerDto Get(int id) => new CustomerDto { Id = id, Name = "Sample" };

    public CustomerDto Create(CustomerDto dto) => dto;
}
