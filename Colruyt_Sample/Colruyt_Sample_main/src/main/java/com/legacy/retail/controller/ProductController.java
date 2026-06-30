package com.legacy.retail.controller;

import com.legacy.retail.model.Product;
import com.legacy.retail.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
public class ProductController {

    @Autowired
    private ProductService productService;

    @GetMapping("/api/products")
    public List<Product> listProducts() {
        return productService.findAll();
    }

    @PostMapping("/api/products")
    public Product createProduct(@RequestBody ProductRequest req) {
        return productService.createProduct(req);
    }

    @PutMapping("/api/products/{id}")
    public ResponseEntity<Product> updateProduct(@PathVariable Long id, @RequestBody ProductRequest req) {
        return ResponseEntity.ok(productService.updateProduct(id, req));
    }

    // Inner request DTO
    public static class ProductRequest {
        private String name;
        private String sku;
        private Double price;
        private Integer stockQuantity;
        private Long categoryId;

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getSku() { return sku; }
        public void setSku(String sku) { this.sku = sku; }
        public Double getPrice() { return price; }
        public void setPrice(Double price) { this.price = price; }
        public Integer getStockQuantity() { return stockQuantity; }
        public void setStockQuantity(Integer stockQuantity) { this.stockQuantity = stockQuantity; }
        public Long getCategoryId() { return categoryId; }
        public void setCategoryId(Long categoryId) { this.categoryId = categoryId; }
    }
}
