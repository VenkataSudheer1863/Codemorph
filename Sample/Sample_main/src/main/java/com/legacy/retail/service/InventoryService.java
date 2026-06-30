package com.legacy.retail.service;

import com.legacy.retail.model.Product;
import com.legacy.retail.repository.ProductRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class InventoryService {

    @Autowired
    private ProductRepository productRepository;

    @Transactional
    public void adjustStock(Long productId, int delta) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new RuntimeException("Product not found: " + productId));
        int updated = product.getStockQuantity() + delta;
        if (updated < 0) {
            throw new IllegalStateException("Stock cannot go below zero for product: " + productId);
        }
        product.setStockQuantity(updated);
        productRepository.save(product);
    }

    public List<Product> getLowStockProducts(int threshold) {
        return productRepository.findLowStockProducts(threshold);
    }

    @Transactional
    public void reserveStock(Long productId, int quantity) {
        adjustStock(productId, -quantity);
    }

    @Transactional
    public void releaseStock(Long productId, int quantity) {
        adjustStock(productId, quantity);
    }
}
