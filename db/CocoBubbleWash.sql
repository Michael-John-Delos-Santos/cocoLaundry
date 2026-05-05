CREATE DATABASE IF NOT EXISTS cocobubblewash;
USE cocobubblewash;

-- 1. Users Table (Integrated with email column)
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL, -- Passwords should be hashed in Python
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    role ENUM('Admin', 'Staff') DEFAULT 'Staff',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME NULL
);

-- Insert default admin account
INSERT IGNORE INTO Users (username, password, full_name, role)
VALUES ('admin', 'admin123', 'System Administrator', 'Admin');


-- 2. Services Table (Updated for pricing per load)
CREATE TABLE IF NOT EXISTS Services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    price_per_load DECIMAL(10, 2) NOT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- 3. Category Table
CREATE TABLE IF NOT EXISTS Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- Insert default categories
INSERT IGNORE INTO Category (name, description) VALUES
('Whites', 'White clothing'),
('Colored', 'Colored clothing'),
('Bedsheets', 'Bedsheets and linens'),
('Delicates', 'Delicate fabrics'),


-- 4. Addons Table
CREATE TABLE IF NOT EXISTS Addons (
    addon_id INT AUTO_INCREMENT PRIMARY KEY,
    addon_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    pricing_type ENUM('Fixed', 'Per Kg') DEFAULT 'Fixed',
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- 5. Transactions Table (Integrated with customer_email)
CREATE TABLE IF NOT EXISTS Transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    display_id VARCHAR(20) NOT NULL UNIQUE,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100) DEFAULT NULL,
    customer_contact VARCHAR(50),
    overall_note TEXT,
    pickup_date DATETIME,
    status ENUM('In-queue', 'Ready to Claim', 'Claimed') DEFAULT 'In-queue',
    payment_status ENUM('Paid', 'Unpaid') DEFAULT 'Unpaid',
    total_amount DECIMAL(10, 2) DEFAULT 0.00,
    created_by INT,
    void_status ENUM('Active', 'Voided') DEFAULT 'Active',
    void_reason TEXT,
    void_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id) ON DELETE SET NULL
);


-- 6. Transaction Batches Table (Integrated with load_count)
CREATE TABLE IF NOT EXISTS Transaction_Batches (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT,
    service_id INT,
    category_id INT,
    load_count INT NOT NULL,
    weight DECIMAL(8, 2) NOT NULL,
    price_per_unit DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    special_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES Services(service_id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE RESTRICT
);


-- 7. Batch Addons Table
CREATE TABLE IF NOT EXISTS Batch_Addons (
    batch_addon_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT,
    addon_id INT,
    quantity DECIMAL(8, 2) DEFAULT 1.00,
    price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES Transaction_Batches(batch_id) ON DELETE CASCADE,
    FOREIGN KEY (addon_id) REFERENCES Addons(addon_id) ON DELETE RESTRICT
);


-- 8. Audit Logs Table (Integrated with REVERT_VOID)
CREATE TABLE IF NOT EXISTS Audit_Logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action_type ENUM('CREATE', 'UPDATE', 'DELETE', 'VOID', 'LOGIN', 'REVERT_VOID') NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT,
    description TEXT,
    old_value TEXT,
    new_value TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL
);


-- 9. Password Resets Table
CREATE TABLE IF NOT EXISTS password_resets (
    reset_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    expiry DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);


-- 10. System Configuration Table
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(50) PRIMARY KEY,
    config_value TEXT
);

-- Initialize Configurations
INSERT IGNORE INTO system_config (config_key, config_value) VALUES 
('admin_email', 'your-business@gmail.com'),
('gmail_app_password', 'yourpassword'),
('otp_subject', 'CocoBubbleWash Password Reset'),
('otp_body', 'Your OTP for password reset is: {otp}. It expires in 10 minutes.'),
('pickup_ready_subject', 'Order Ready for Pickup'),
('pickup_ready_body', 'Your load is marked as complete and ready for pickup!'),
('kg_per_load', '7');