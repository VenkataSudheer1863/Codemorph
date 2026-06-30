package com.legacy.retail.soap;

import javax.jws.WebMethod;
import javax.jws.WebParam;
import javax.jws.WebService;
import java.util.ArrayList;
import java.util.List;

@WebService(serviceName = "LegacyReportService",
            targetNamespace = "http://soap.retail.legacy.com/")
public class LegacyReportService {

    @WebMethod(operationName = "getOrderReport")
    public String getOrderReport(@WebParam(name = "customerId") Long customerId) {
        return "Order report for customer: " + customerId;
    }

    @WebMethod(operationName = "getSalesSummary")
    public List<String> getSalesSummary(@WebParam(name = "month") int month,
                                         @WebParam(name = "year") int year) {
        List<String> summary = new ArrayList<>();
        summary.add("Month: " + month + "/" + year);
        summary.add("Total Orders: 0");
        summary.add("Total Revenue: $0.00");
        return summary;
    }

    @WebMethod(operationName = "getInventoryReport")
    public String getInventoryReport() {
        return "Inventory report generated at: " + System.currentTimeMillis();
    }

    @WebMethod(operationName = "getLowStockAlert")
    public List<String> getLowStockAlert(@WebParam(name = "threshold") int threshold) {
        // Returns SKUs with stock below threshold
        return new ArrayList<>();
    }
}
