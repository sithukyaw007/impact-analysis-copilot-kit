import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Order } from './order.model';

@Injectable({ providedIn: 'root' })
export class OrderService {
  constructor(private http: HttpClient) {}

  getAll() {
    return this.http.get<Order[]>('/api/orders');
  }

  getById(id: number) {
    return this.http.get<Order>(`/api/orders/${id}`);
  }

  create(order: Order) {
    return this.http.post<Order>('/api/orders', order);
  }
}
