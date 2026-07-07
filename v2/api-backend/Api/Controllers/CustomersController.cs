using Application.Customers;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class CustomersController : ControllerBase
{
    private readonly ICustomerService _customers;

    public CustomersController(ICustomerService customers)
    {
        _customers = customers;
    }

    [HttpGet("{id}")]
    public CustomerDto GetById(int id) => _customers.Get(id);

    [HttpPost]
    public CustomerDto Create(CustomerDto dto) => _customers.Create(dto);
}
