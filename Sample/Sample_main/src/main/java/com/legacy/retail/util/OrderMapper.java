package com.legacy.retail.util;

import com.legacy.retail.model.Order;

import java.util.HashMap;
import java.util.Map;

/**
 * Manual mapper — no MapStruct/ModelMapper, intentional legacy pattern.
 */
public class OrderMapper {

    public static Map<String, Object> toMap(Order order) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", order.getId());
        map.put("customerId", order.getCustomerId());
        map.put("status", order.getStatus());
        map.put("totalAmount", order.getTotalAmount());
        map.put("createdAt", order.getCreatedAt() != null ? order.getCreatedAt().toString() : null);
        map.put("updatedAt", order.getUpdatedAt() != null ? order.getUpdatedAt().toString() : null);
        return map;
    }

    public static Order fromMap(Map<String, Object> map) {
        Order order = new Order();
        order.setCustomerId(Long.valueOf(map.get("customerId").toString()));
        order.setStatus((String) map.get("status"));
        order.setTotalAmount(Double.valueOf(map.get("totalAmount").toString()));
        return order;
    }
}
