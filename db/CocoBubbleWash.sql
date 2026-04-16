-- =============================================
-- Database: CocoBubbleWashDB
-- Description: Full schema with OTP and Email integration
-- =============================================

CREATE DATABASE IF NOT EXISTS CocoBubbleWashDB;
USE CocoBubbleWashDB;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    role ENUM('Admin', 'Staff') DEFAULT 'Staff',
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- 2. Password Resets (Standalone OTP Table)
CREATE TABLE IF NOT EXISTS password_resets (
    reset_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    expiry DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 3. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);

-- 4. Services Table
CREATE TABLE IF NOT EXISTS services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    price_per_kg DECIMAL(10,2) NOT NULL,
    base_price DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 5. Addons Table
CREATE TABLE IF NOT EXISTS addons (
    addon_id INT AUTO_INCREMENT PRIMARY KEY,
    addon_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    pricing_type ENUM('Fixed', 'Per Kg') DEFAULT 'Fixed',
    status ENUM('Active', 'Inactive') DEFAULT 'Active'
);

-- 6. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    display_id VARCHAR(20),
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100), -- Optional for notification
    customer_contact VARCHAR(20),
    overall_note TEXT,
    pickup_date DATE,
    status ENUM('in-queue', 'ready to claim', 'claimed') DEFAULT 'in-queue',
    payment_status ENUM('Paid', 'Unpaid') DEFAULT 'Unpaid',
    total_amount DECIMAL(10,2) NOT NULL,
    created_by INT,
    void_status ENUM('active', 'voided') DEFAULT 'active',
    void_reason TEXT,
    void_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- 7. Transaction Batches Table
CREATE TABLE IF NOT EXISTS transaction_batches (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT,
    service_id INT,
    category_id INT,
    weight DECIMAL(10,2),
    price_per_unit DECIMAL(10,2),
    subtotal DECIMAL(10,2),
    special_notes TEXT,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- 8. Batch Addons Table
CREATE TABLE IF NOT EXISTS batch_addons (
    batch_addon_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT,
    addon_id INT,
    quantity INT DEFAULT 1,
    price DECIMAL(10,2),
    subtotal DECIMAL(10,2),
    FOREIGN KEY (batch_id) REFERENCES transaction_batches(batch_id) ON DELETE CASCADE,
    FOREIGN KEY (addon_id) REFERENCES addons(addon_id)
);

-- 9. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action_type ENUM('CREATE', 'UPDATE', 'DELETE', 'VOID'),
    entity_type VARCHAR(50),
    entity_id INT,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- =============================================
-- SAMPLE DATA & OPERATIONS
-- =============================================

-- Initial Admin User (Default PW: admin123)
INSERT INTO users (username, password, email, full_name, role) 
VALUES ('admin', 'admin123', 'admin@cocobubble.com', 'System Admin', 'Admin');

-- ---------------------------------------------
-- QUERY: VALIDATE OTP (For Forgot Password)
-- ---------------------------------------------
-- SELECT r.user_id, r.reset_id 
-- FROM password_resets r
-- JOIN users u ON r.user_id = u.user_id
-- WHERE u.email = 'target@email.com' 
-- AND r.otp_code = '123456' 
-- AND r.is_used = FALSE 
-- AND r.expiry > NOW();

-- ---------------------------------------------
-- QUERY: UPDATE PASSWORD & CONSUME OTP
-- ---------------------------------------------
-- UPDATE users SET password = 'new_secure_password' WHERE user_id = 1;
-- UPDATE password_resets SET is_used = TRUE WHERE reset_id = 5;