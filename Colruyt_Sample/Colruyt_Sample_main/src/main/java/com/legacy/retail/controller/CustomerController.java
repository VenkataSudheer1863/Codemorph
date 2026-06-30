package com.legacy.retail.controller;

import com.legacy.retail.model.Customer;
import com.legacy.retail.repository.CustomerRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
public class CustomerController {

    @Autowired
    private CustomerRepository customerRepository;

    @GetMapping("/api/customers")
    public List<Customer> listCustomers() {
        return customerRepository.findAll();
    }

    @PostMapping("/api/customers")
    public Customer createCustomer(@RequestBody CustomerRequest req) {
        Customer customer = new Customer();
        customer.setFirstName(req.getFirstName());
        customer.setLastName(req.getLastName());
        customer.setEmail(req.getEmail());
        customer.setPhone(req.getPhone());
        customer.setAddress(req.getAddress());
        return customerRepository.save(customer);
    }

    @DeleteMapping("/api/customers/{id}")
    public ResponseEntity<Void> deleteCustomer(@PathVariable Long id) {
        customerRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }

    // Inner request DTO
    public static class CustomerRequest {
        private String firstName;
        private String lastName;
        private String email;
        private String phone;
        private String address;

        public String getFirstName() { return firstName; }
        public void setFirstName(String firstName) { this.firstName = firstName; }
        public String getLastName() { return lastName; }
        public void setLastName(String lastName) { this.lastName = lastName; }
        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }
        public String getPhone() { return phone; }
        public void setPhone(String phone) { this.phone = phone; }
        public String getAddress() { return address; }
        public void setAddress(String address) { this.address = address; }
    }
}
