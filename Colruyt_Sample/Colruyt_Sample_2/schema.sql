CREATE DATABASE IF NOT EXISTS spendwise;
USE spendwise;

CREATE TABLE IF NOT EXISTS expenses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    amount DOUBLE NOT NULL,
    category VARCHAR(255),
    is_recurring BOOLEAN DEFAULT FALSE,
    date DATE
);
