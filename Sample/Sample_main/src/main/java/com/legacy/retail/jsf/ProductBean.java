package com.legacy.retail.jsf;

import com.legacy.retail.controller.ProductController.ProductRequest;
import com.legacy.retail.model.Product;
import com.legacy.retail.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.faces.bean.ManagedBean;
import javax.faces.bean.ViewScoped;
import java.io.Serializable;
import java.util.List;

@ManagedBean(name = "productBean")
@ViewScoped
@Component
public class ProductBean implements Serializable {

    private static final long serialVersionUID = 1L;

    @Autowired
    private ProductService productService;

    private String name;
    private String sku;
    private Double price;
    private Integer stockQuantity;
    private Long categoryId;
    private List<Product> products;

    public String createProduct() {
        ProductRequest req = new ProductRequest();
        req.setName(name);
        req.setSku(sku);
        req.setPrice(price);
        req.setStockQuantity(stockQuantity != null ? stockQuantity : 0);
        req.setCategoryId(categoryId);
        productService.createProduct(req);
        loadProducts();
        return null;
    }

    public List<Product> getProducts() {
        if (products == null) {
            loadProducts();
        }
        return products;
    }

    private void loadProducts() {
        this.products = productService.findAll();
    }

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
    public void setProducts(List<Product> products) { this.products = products; }
}
