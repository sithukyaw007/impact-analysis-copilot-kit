import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Customer } from './customer.model';

@Injectable({ providedIn: 'root' })
export class CustomerService {
  constructor(private http: HttpClient) {}

  getById(id: number) {
    return this.http.get<Customer>(`/api/customers/${id}`);
  }

  create(customer: Customer) {
    return this.http.post<Customer>('/api/customers', customer);
  }
}
