package com.legacy.retail.jsf;

import com.legacy.retail.controller.OrderController.OrderRequest;
import com.legacy.retail.model.Order;
import com.legacy.retail.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.faces.bean.ManagedBean;
import javax.faces.bean.ViewScoped;
import java.io.Serializable;
import java.util.List;

@ManagedBean(name = "orderBean")
@ViewScoped
@Component
public class OrderBean implements Serializable {

    private static final long serialVersionUID = 1L;

    @Autowired
    private OrderService orderService;

    private Long customerId;
    private Double totalAmount;
    private List<Order> orders;

    public String createOrder() {
        OrderRequest req = new OrderRequest();
        req.setCustomerId(customerId);
        req.setTotalAmount(totalAmount);
        req.setStatus("PENDING");
        orderService.createOrder(req);
        loadOrders();
        return null; // stay on same page
    }

    public String deleteOrder(Long id) {
        orderService.deleteOrder(id);
        loadOrders();
        return null;
    }

    public List<Order> getOrders() {
        if (orders == null) {
            loadOrders();
        }
        return orders;
    }

    private void loadOrders() {
        this.orders = orderService.findAll();
    }

    public Long getCustomerId() { return customerId; }
    public void setCustomerId(Long customerId) { this.customerId = customerId; }
    public Double getTotalAmount() { return totalAmount; }
    public void setTotalAmount(Double totalAmount) { this.totalAmount = totalAmount; }
    public void setOrders(List<Order> orders) { this.orders = orders; }
}
