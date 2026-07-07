export interface Order {
  id: number;
  customerId: number;
  // v2: renamed from `total`, added `currency` to mirror the backend OrderDto.
  totalAmount: number;
  currency: string;
  status: string;
}
