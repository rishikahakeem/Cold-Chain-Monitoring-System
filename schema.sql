CREATE DATABASE IF NOT EXISTS yottaflex_test_db;
USE yottaflex_test_db;

-- 1. PRODUCT TABLE
CREATE TABLE products (
    product_id VARCHAR(30) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    min_temperature DECIMAL(5,2) NOT NULL,
    max_temperature DECIMAL(5,2) NOT NULL,
    min_humidity DECIMAL(5,2) DEFAULT 0,
    max_humidity DECIMAL(5,2) DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. THRESHOLD POLICY TABLE
CREATE TABLE threshold_policies (
    policy_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(30) NOT NULL,
    max_excursion_minutes INT NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE DEFAULT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 3. SHIPMENT TABLE
CREATE TABLE shipments (
    shipment_id VARCHAR(30) PRIMARY KEY,
    product_id VARCHAR(30) NOT NULL,
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    departure_time DATETIME,
    expected_arrival DATETIME,
    actual_arrival DATETIME,
    shipment_status VARCHAR(30) DEFAULT 'PLANNED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 4. CONTAINER TABLE
CREATE TABLE containers (
    container_id VARCHAR(30) PRIMARY KEY,
    shipment_id VARCHAR(30) NOT NULL,
    container_type VARCHAR(50),
    container_status VARCHAR(30) DEFAULT 'ACTIVE',
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

-- 5. SENSOR TABLE
CREATE TABLE sensors (
    sensor_id VARCHAR(50) PRIMARY KEY,
    container_id VARCHAR(30) NOT NULL,
    sensor_type VARCHAR(30) NOT NULL,
    calibration_status VARCHAR(30) DEFAULT 'CALIBRATED',
    last_calibrated DATETIME,
    FOREIGN KEY (container_id) REFERENCES containers(container_id)
);

-- 6. ROUTE STOP TABLE
CREATE TABLE route_stops (
    stop_id INT AUTO_INCREMENT PRIMARY KEY,
    shipment_id VARCHAR(30) NOT NULL,
    stop_number INT NOT NULL,
    location VARCHAR(100) NOT NULL,
    arrival_time DATETIME,
    departure_time DATETIME,
    stop_status VARCHAR(30) DEFAULT 'PENDING',
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    UNIQUE (shipment_id, stop_number)
);

-- 7. SENSOR READING TABLE
CREATE TABLE sensor_readings (
    reading_id VARCHAR(100) PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    shipment_id VARCHAR(30) NOT NULL,
    stop_id INT,
    temperature DECIMAL(6,2) NOT NULL,
    humidity DECIMAL(6,2) NOT NULL,
    reading_time DATETIME NOT NULL,
    data_status VARCHAR(30) DEFAULT 'VALID',
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id),
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    FOREIGN KEY (stop_id) REFERENCES route_stops(stop_id),
    INDEX idx_reading_time (reading_time),
    INDEX idx_shipment_time (shipment_id, reading_time)
);

-- 8. EXCURSION TABLE
CREATE TABLE excursions (
    excursion_id VARCHAR(30) PRIMARY KEY,
    shipment_id VARCHAR(30) NOT NULL,
    sensor_id VARCHAR(50) NOT NULL,
    excursion_type VARCHAR(30) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_minutes DECIMAL(10,2) DEFAULT 0,
    maximum_temperature DECIMAL(6,2),
    excursion_status VARCHAR(30) DEFAULT 'OPEN',
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id)
);

-- 9. CUSTODY EVENT TABLE
CREATE TABLE custody_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    shipment_id VARCHAR(30) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    responsible_person VARCHAR(100),
    event_location VARCHAR(100),
    event_time DATETIME NOT NULL,
    remarks TEXT,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    INDEX idx_custody_time (shipment_id, event_time)
);

-- 10. CORRECTIVE ACTION TABLE
CREATE TABLE corrective_actions (
    action_id INT AUTO_INCREMENT PRIMARY KEY,
    excursion_id VARCHAR(30),
    shipment_id VARCHAR(30) NOT NULL,
    action_description TEXT NOT NULL,
    assigned_to VARCHAR(100),
    action_status VARCHAR(30) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (excursion_id) REFERENCES excursions(excursion_id),
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

-- SAMPLE PRODUCT DATA
INSERT INTO products
(product_id, product_name, category,
 min_temperature, max_temperature,
 min_humidity, max_humidity)
VALUES
('PRD-001', 'Vaccines', 'Pharmaceutical',
 2, 8, 30, 60),

('PRD-002', 'Fresh Fruits', 'Food',
 2, 10, 60, 90),

('PRD-003', 'Frozen Food', 'Food',
 -25, -18, 40, 80);

-- SAMPLE THRESHOLD POLICIES
INSERT INTO threshold_policies
(product_id, max_excursion_minutes, effective_from)
VALUES
('PRD-001', 15, '2026-01-01'),
('PRD-002', 30, '2026-01-01'),
('PRD-003', 20, '2026-01-01');

-- CHECK DATABASE
SHOW TABLES;

SELECT * FROM products;
SELECT * FROM threshold_policies;
