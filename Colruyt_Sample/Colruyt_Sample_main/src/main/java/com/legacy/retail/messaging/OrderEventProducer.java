package com.legacy.retail.messaging;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.logging.Logger;

@Component
public class OrderEventProducer {

    private static final Logger logger = Logger.getLogger(OrderEventProducer.class.getName());
    private static final String ORDERS_TOPIC = "order-events";

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    public void publishOrderCreated(Long orderId) {
        String message = "{\"event\":\"ORDER_CREATED\",\"orderId\":" + orderId + "}";
        kafkaTemplate.send(ORDERS_TOPIC, String.valueOf(orderId), message);
        logger.info("Published ORDER_CREATED event for order: " + orderId);
    }

    public void publishOrderStatusChanged(Long orderId, String newStatus) {
        String message = "{\"event\":\"STATUS_CHANGED\",\"orderId\":" + orderId
                + ",\"status\":\"" + newStatus + "\"}";
        kafkaTemplate.send(ORDERS_TOPIC, String.valueOf(orderId), message);
    }

    // Legacy low-level producer usage
    public void publishLegacyEvent(String topic, String key, String value) {
        KafkaProducer<String, String> legacyProducer = KafkaProducerFactory.createProducer();
        try {
            legacyProducer.send(new ProducerRecord<>(topic, key, value));
        } finally {
            legacyProducer.close();
        }
    }

    @KafkaListener(topics = "order-dlq", groupId = "retail-dlq-group")
    public void handleDeadLetterOrder(String message) {
        logger.warning("Dead letter order event received: " + message);
    }
}
