package com.legacy.retail.repository;

import com.legacy.retail.model.Order;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    List<Order> findByCustomerId(Long customerId);

    List<Order> findByStatus(String status);

    @Query("SELECT o FROM Order o WHERE o.customerId = :customerId AND o.status = :status")
    List<Order> findByCustomerIdAndStatus(@Param("customerId") Long customerId,
                                          @Param("status") String status);

    @Query("SELECT o FROM Order o WHERE o.totalAmount >= :minAmount ORDER BY o.createdAt DESC")
    List<Order> findOrdersAboveAmount(@Param("minAmount") Double minAmount);

    @Query(value = "SELECT * FROM orders WHERE DATE(created_at) = CURDATE()", nativeQuery = true)
    List<Order> findTodaysOrders();
}
