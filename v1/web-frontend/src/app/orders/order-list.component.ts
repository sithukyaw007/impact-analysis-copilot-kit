import { Component, OnInit } from '@angular/core';
import { OrderService } from './order.service';
import { Order } from './order.model';

@Component({ selector: 'app-order-list', template: '<div></div>' })
export class OrderListComponent implements OnInit {
  orders: Order[] = [];

  constructor(private orderService: OrderService) {}

  ngOnInit(): void {
    this.orderService.getAll().subscribe(o => (this.orders = o));
  }
}
