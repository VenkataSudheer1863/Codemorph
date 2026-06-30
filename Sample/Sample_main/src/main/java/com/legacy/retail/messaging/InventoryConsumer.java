package com.legacy.retail.messaging;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.logging.Logger;

@Component
public class InventoryConsumer {

    private static final Logger logger = Logger.getLogger(InventoryConsumer.class.getName());

    @KafkaListener(topics = "inventory-updates", groupId = "retail-inventory-group")
    public void handleInventoryUpdate(String message) {
        logger.info("Received inventory update: " + message);
        processInventoryEvent(message);
    }

    @KafkaListener(topics = "inventory-alerts", groupId = "retail-inventory-group")
    public void handleInventoryAlert(String message) {
        logger.warning("Inventory alert received: " + message);
    }

    private void processInventoryEvent(String message) {
        // Parse and apply inventory delta from message payload
        logger.info("Processing inventory event: " + message);
    }
}
