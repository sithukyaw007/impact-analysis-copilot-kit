namespace Application.Orders;

public record OrderDto
{
    public int Id { get; set; }
    public int CustomerId { get; set; }
    public decimal Total { get; set; }
    public string Status { get; set; } = "Pending";
}
