
-- ============================================================================
-- SingleStore Database Schema for Churn Prediction
-- ============================================================================

-- Use database
USE churn_db;

-- ==========================================
-- 1. CUSTOMERS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    signup_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    senior_citizen TINYINT DEFAULT 0,
    last_contact_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_status (status),
    KEY idx_signup_date (signup_date)
);

-- ==========================================
-- 2. BILLING TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS billing (
    billing_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    monthly_charges DECIMAL(10, 2) NOT NULL,
    total_charges DECIMAL(10, 2) NOT NULL,
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    last_payment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id)
);

-- ==========================================
-- 3. SERVICE CALLS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS service_calls (
    service_call_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    call_date DATE NOT NULL,
    issue_type VARCHAR(50),
    resolution_time_hours DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id),
    KEY idx_call_date (call_date)
);

-- ==========================================
-- 4. CONTRACTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS contracts (
    contract_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    contract_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    auto_renew TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id),
    KEY idx_contract_type (contract_type)
);

-- ==========================================
-- 5. CUSTOMER FEATURES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS customer_features (
    feature_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    paperless_billing_score TINYINT DEFAULT 0,
    tech_support_score TINYINT DEFAULT 0,
    online_backup_score TINYINT DEFAULT 0,
    streaming_tv_score TINYINT DEFAULT 0,
    streaming_movies_score TINYINT DEFAULT 0,
    device_protection_score TINYINT DEFAULT 0,
    online_security_score TINYINT DEFAULT 0,
    internet_service_score TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id)
);

-- ==========================================
-- 6. PAYMENT METHODS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS payment_methods (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    is_auto_pay TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id)
);

-- ==========================================
-- 7. CHURN HISTORY TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS churn_history (
    churn_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    churn_date DATE NOT NULL,
    churn_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    KEY idx_customer_id (customer_id),
    KEY idx_churn_date (churn_date)
);

-- ==========================================
-- Create View for 30-day Service Calls
-- ==========================================
CREATE OR REPLACE VIEW service_calls_summary AS
SELECT 
    customer_id,
    COUNT(*) as service_calls_30d
FROM service_calls
WHERE call_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY customer_id;

-- ==========================================
-- Verify Tables Created
-- ==========================================
SHOW TABLES;
