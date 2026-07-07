namespace Application.Orders;

public record OrderDto
{
    public int Id { get; set; }
    public int CustomerId { get; set; }

    // v2: renamed from `Total` and split money into amount + currency.
    public decimal TotalAmount { get; set; }
    public string Currency { get; set; } = "SGD";

    public string Status { get; set; } = "Pending";
}
