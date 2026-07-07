import { Component, Input } from '@angular/core';
import { OrderService } from './order.service';
import { Order } from './order.model';

@Component({ selector: 'app-order-detail', template: '<div></div>' })
export class OrderDetailComponent {
  @Input() id = 0;
  order?: Order;

  constructor(private orderService: OrderService) {}

  load(): void {
    this.orderService.getById(this.id).subscribe(o => (this.order = o));
  }
}
