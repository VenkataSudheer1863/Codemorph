package com.legacy.retail.util;

import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Legacy date utility — uses old java.util.Date and SimpleDateFormat
 * intentionally to represent pre-Java8 patterns for migration analysis.
 */
public class DateUtils {

    private static final String DEFAULT_FORMAT = "yyyy-MM-dd HH:mm:ss";

    public static String formatDate(Date date) {
        if (date == null) return "";
        return new SimpleDateFormat(DEFAULT_FORMAT).format(date);
    }

    public static Date parseDate(String dateStr) {
        try {
            return new SimpleDateFormat(DEFAULT_FORMAT).parse(dateStr);
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse date: " + dateStr, e);
        }
    }

    public static boolean isExpired(Date date, long ttlMillis) {
        return System.currentTimeMillis() - date.getTime() > ttlMillis;
    }
}
