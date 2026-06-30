package com.legacy.retail.soap;

import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import javax.xml.ws.Endpoint;
import java.util.logging.Logger;

@Component
public class SoapEndpointPublisher {

    private static final Logger logger = Logger.getLogger(SoapEndpointPublisher.class.getName());

    @EventListener(ApplicationReadyEvent.class)
    public void publishSoapEndpoint() {
        try {
            Endpoint.publish("http://localhost:8080/ws/reports", new LegacyReportService());
            logger.info("SOAP endpoint published at: http://localhost:8080/ws/reports?wsdl");
        } catch (Exception e) {
            logger.warning("Could not publish SOAP endpoint: " + e.getMessage());
        }
    }
}
