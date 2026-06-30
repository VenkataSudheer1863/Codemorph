package com.legacy.retail.service;

import com.legacy.retail.controller.ProductController.ProductRequest;
import com.legacy.retail.model.Product;
import com.legacy.retail.repository.ProductRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ProductService {

    @Autowired
    private ProductRepository productRepository;

    public List<Product> findAll() {
        return productRepository.findAll();
    }

    public Product createProduct(ProductRequest req) {
        Product product = new Product();
        product.setName(req.getName());
        product.setSku(req.getSku());
        product.setPrice(req.getPrice());
        product.setStockQuantity(req.getStockQuantity() != null ? req.getStockQuantity() : 0);
        product.setCategoryId(req.getCategoryId());
        return productRepository.save(product);
    }

    public Product updateProduct(Long id, ProductRequest req) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Product not found: " + id));
        product.setName(req.getName());
        product.setSku(req.getSku());
        product.setPrice(req.getPrice());
        product.setStockQuantity(req.getStockQuantity());
        product.setCategoryId(req.getCategoryId());
        return productRepository.save(product);
    }

    public void deleteProduct(Long id) {
        productRepository.deleteById(id);
    }
}
