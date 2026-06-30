package com.spendwise.entity;

import jakarta.persistence.*;
import java.util.Date;

@Entity
@Table(name = "expenses")
public class Expense {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String description;

    @Column(nullable = false)
    private Double amount;

    private String category;

    @Column(name = "is_recurring")
    private Boolean isRecurring;

    @Temporal(TemporalType.DATE)
    private Date date;

    public Expense() {}

    public Expense(String description, Double amount, String category, Boolean isRecurring, Date date) {
        this.description = description;
        this.amount = amount;
        this.category = category;
        this.isRecurring = isRecurring;
        this.date = date;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public Double getAmount() { return amount; }
    public void setAmount(Double amount) { this.amount = amount; }
    
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    
    public Boolean getIsRecurring() { return isRecurring; }
    public void setIsRecurring(Boolean isRecurring) { this.isRecurring = isRecurring; }
    
    public Date getDate() { return date; }
    public void setDate(Date date) { this.date = date; }
}
