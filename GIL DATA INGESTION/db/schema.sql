CREATE DATABASE IF NOT EXISTS gil_db;

USE gil_db;

CREATE TABLE IF NOT EXISTS plant_metadata (
    plant_id INT AUTO_INCREMENT PRIMARY KEY,
    plant_name VARCHAR(100) NOT NULL,
    plant_type ENUM('WIND', 'SOLAR', 'HYBRID') NOT NULL,
    location VARCHAR(255),
    capacity_mw DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_plant_type (plant_type)
);

CREATE TABLE IF NOT EXISTS wind_generation (
    wind_gen_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    serial_number VARCHAR(100) NOT NULL,
    generation_date DATE NOT NULL,
    generation_time TIME NOT NULL,
    generation_value DECIMAL(14,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plant_metadata(plant_id),
    UNIQUE KEY unique_wind_record (
        serial_number,
        generation_date,
        generation_time
    ),
    INDEX idx_wind_date (generation_date),
    INDEX idx_wind_serial (serial_number),
    INDEX idx_wind_plant (plant_id)
);

CREATE TABLE IF NOT EXISTS solar_generation (
    solar_gen_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    serial_number VARCHAR(100) NOT NULL,
    generation_date DATE NOT NULL,
    generation_time TIME NOT NULL,
    generation_value DECIMAL(14,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plant_metadata(plant_id),
    UNIQUE KEY unique_solar_record (
        serial_number,
        generation_date,
        generation_time
    ),
    INDEX idx_solar_date (generation_date),
    INDEX idx_solar_serial (serial_number),
    INDEX idx_solar_plant (plant_id)
);

CREATE TABLE IF NOT EXISTS consumption_data (
    consumption_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    consumption_date DATE NOT NULL,
    consumption_time TIME NOT NULL,
    consumption_value DECIMAL(14,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_consumption (
        consumption_date,
        consumption_time
    ),
    INDEX idx_consumption_date (consumption_date)
);

CREATE TABLE IF NOT EXISTS settlement_matching (
    matching_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    settlement_date DATE NOT NULL,
    settlement_time TIME NOT NULL,
    plant_id INT NOT NULL,
    serial_number VARCHAR(100) NOT NULL,
    generation_type ENUM('WIND','SOLAR') NOT NULL,
    generation_value DECIMAL(14,4) DEFAULT 0,
    slot_total_consumption DECIMAL(14,4) DEFAULT 0,
    allocated_consumption DECIMAL(14,4) DEFAULT 0,
    surplus_generation DECIMAL(14,4) DEFAULT 0,
    surplus_gen_with_banking DECIMAL(14,4) DEFAULT 0,
    matched_settlement DECIMAL(14,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plant_metadata(plant_id),
    UNIQUE KEY unique_matching_record (
        serial_number,
        settlement_date,
        settlement_time
    ),
    INDEX idx_matching_date (settlement_date),
    INDEX idx_matching_datetime (
        settlement_date,
        settlement_time
    ),
    INDEX idx_matching_serial (serial_number),
    INDEX idx_matching_plant (plant_id)
);

CREATE TABLE IF NOT EXISTS slot_summary (
    slot_summary_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    summary_date DATE NOT NULL,
    summary_time TIME NOT NULL,
    generation_value DECIMAL(14,4),
    slot_total_consumption DECIMAL(14,4),
    allocated_consumption DECIMAL(14,4),
    surplus_generation DECIMAL(14,4),
    surplus_gen_with_banking DECIMAL(14,4),
    matched_settlement DECIMAL(14,4),
    UNIQUE KEY unique_slot_summary (
        summary_date,
        summary_time
    ),
    INDEX idx_slot_summary_date (summary_date)
);

CREATE TABLE IF NOT EXISTS tod_daily_summary (
    tod_daily_summary_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    summary_date DATE NOT NULL,
    tod_slot VARCHAR(100) NOT NULL,
    generation_value DECIMAL(14,4),
    allocated_consumption DECIMAL(14,4),
    matched_settlement DECIMAL(14,4),
    surplus_demand DECIMAL(14,4),
    surplus_generation DECIMAL(14,4),
    surplus_gen_with_banking DECIMAL(14,4),
    slot_total_consumption DECIMAL(14,4),
    matched_settlement_daily_tod DECIMAL(14,4),
    surplus_gen_daily_tod DECIMAL(14,4),
    surplus_demand_daily_tod DECIMAL(14,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_tod_daily (
        summary_date,
        tod_slot
    ),
    INDEX idx_tod_daily_date (summary_date)
);

CREATE TABLE IF NOT EXISTS monthly_banking_settlement (
    banking_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    settlement_month CHAR(7) NOT NULL,
    tod_slot VARCHAR(100) NOT NULL,
    generation_value DECIMAL(14,4),
    allocated_consumption DECIMAL(14,4),
    matched_settlement DECIMAL(14,4),
    surplus_demand DECIMAL(14,4),
    surplus_generation DECIMAL(14,4),
    surplus_gen_with_banking DECIMAL(14,4),
    slot_total_consumption DECIMAL(14,4),
    matched_settlement_daily_tod DECIMAL(14,4),
    surplus_gen_daily_tod DECIMAL(14,4),
    surplus_demand_daily_tod DECIMAL(14,4),
    matched_settlement_intra_monthly DECIMAL(14,4),
    surplus_gen_intra_monthly DECIMAL(14,4),
    surplus_demand_intra_monthly DECIMAL(14,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_month_tod (
        settlement_month,
        tod_slot
    ),
    INDEX idx_banking_month (settlement_month)
);

CREATE TABLE IF NOT EXISTS savings_summary (
    savings_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    settlement_month DATE NOT NULL,
    total_consumption DECIMAL(14,4),
    grid_cost DECIMAL(14,4),
    actual_cost_with_banking DECIMAL(14,4),
    savings_with_banking DECIMAL(14,4),
    savings_pct_with_banking DECIMAL(6,2),
    actual_cost_without_banking DECIMAL(14,4),
    savings_without_banking DECIMAL(14,4),
    savings_pct_without_banking DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_savings_month (settlement_month)
);
