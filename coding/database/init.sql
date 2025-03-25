-- Create the hotel database if it doesn't exist
CREATE DATABASE IF NOT EXISTS hotel;
USE hotel;

-- Create rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) NOT NULL UNIQUE,
    room_type ENUM('single', 'double', 'family') NOT NULL,
    price_per_night DECIMAL(10, 2) NOT NULL,
    floor INT NOT NULL,
    status ENUM('available', 'occupied', 'maintenance', 'cleaning') NOT NULL DEFAULT 'available',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_room_type (room_type),
    INDEX idx_status (status)
);

-- Create cleaning_tasks table
CREATE TABLE IF NOT EXISTS cleaning_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    staff_id INT,
    status ENUM('pending', 'in_progress', 'completed', 'verified') NOT NULL DEFAULT 'pending',
    scheduled_at DATETIME NOT NULL,
    started_at DATETIME,
    completed_at DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_room_id (room_id),
    INDEX idx_staff_id (staff_id),
    INDEX idx_status (status)
);

-- Create room_availability table
CREATE TABLE IF NOT EXISTS room_availability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_type ENUM('single', 'double', 'family') NOT NULL,
    date DATE NOT NULL,
    available_count INT NOT NULL DEFAULT 0,
    base_price DECIMAL(10, 2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_room_type_date (room_type, date)
);

-- Create staff table
CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role ENUM('staff', 'admin') NOT NULL DEFAULT 'staff',
    department ENUM('housekeeping', 'frontdesk', 'maintenance') NOT NULL,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_department (department),
    INDEX idx_status (status)
);
