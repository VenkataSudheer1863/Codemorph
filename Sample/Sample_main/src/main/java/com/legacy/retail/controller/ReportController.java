package com.legacy.retail.controller;

import com.legacy.retail.service.OrderService;
import com.legacy.retail.service.InventoryService;
import com.legacy.retail.model.Order;
import com.legacy.retail.model.Product;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/reports")
public class ReportController {

    @Autowired
    private OrderService orderService;

    @Autowired
    private InventoryService inventoryService;

    @GetMapping("/orders/customer/{customerId}")
    public List<Order> getOrdersByCustomer(@PathVariable Long customerId) {
        return orderService.findByCustomerId(customerId);
    }

    @GetMapping("/inventory/low-stock")
    public List<Product> getLowStockReport(@RequestParam(defaultValue = "10") int threshold) {
        return inventoryService.getLowStockProducts(threshold);
    }

    @GetMapping("/summary")
    public Map<String, Object> getSummary() {
        Map<String, Object> summary = new HashMap<>();
        summary.put("totalOrders", orderService.findAll().size());
        summary.put("lowStockItems", inventoryService.getLowStockProducts(10).size());
        return summary;
    }
}
