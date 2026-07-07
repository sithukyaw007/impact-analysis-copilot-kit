import { Component, Input } from '@angular/core';
import { CustomerService } from './customer.service';
import { Customer } from './customer.model';

@Component({ selector: 'app-customer-detail', template: '<div></div>' })
export class CustomerDetailComponent {
  @Input() id = 0;
  customer?: Customer;

  constructor(private customerService: CustomerService) {}

  load(): void {
    this.customerService.getById(this.id).subscribe(c => (this.customer = c));
  }
}
