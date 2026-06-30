package com.legacy.retail.ejb;

import javax.ejb.EJB;
import javax.ejb.Stateless;
import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import java.util.logging.Logger;

@Stateless
public class InventoryBean {

    private static final Logger logger = Logger.getLogger(InventoryBean.class.getName());

    @PersistenceContext(unitName = "retailPU")
    private EntityManager em;

    @EJB
    private InventoryBean self;

    public void adjustStock(Long productId, int delta) {
        em.createQuery("UPDATE Product p SET p.stockQuantity = p.stockQuantity + :delta WHERE p.id = :id")
                .setParameter("delta", delta)
                .setParameter("id", productId)
                .executeUpdate();
    }

    public int getStockLevel(Long productId) {
        Long count = (Long) em.createQuery(
                "SELECT p.stockQuantity FROM Product p WHERE p.id = :id")
                .setParameter("id", productId)
                .getSingleResult();
        return count != null ? count.intValue() : 0;
    }

    public Object lookupService(String jndiName) {
        try {
            Context ctx = new InitialContext();
            return ctx.lookup(jndiName);
        } catch (NamingException e) {
            logger.severe("JNDI lookup failed for: " + jndiName);
            throw new RuntimeException("JNDI lookup error", e);
        }
    }

    public void reserveInventory(Long productId, int quantity) {
        int current = getStockLevel(productId);
        if (current < quantity) {
            throw new IllegalStateException("Insufficient stock for product: " + productId);
        }
        adjustStock(productId, -quantity);
    }
}
