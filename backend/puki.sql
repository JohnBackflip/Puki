DROP DATABASE IF EXISTS puki;
CREATE DATABASE IF NOT EXISTS puki;
USE puki;

-- Guest table
CREATE TABLE IF NOT EXISTS guest (
  guest_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  email VARCHAR(128) UNIQUE NOT NULL,
  contact VARCHAR(15) UNIQUE NOT NULL
);

-- Room table
CREATE TABLE IF NOT EXISTS room (
    room_id VARCHAR(5) PRIMARY KEY NOT NULL, 
    room_type ENUM('Single', 'Family', 'PresidentialSuite') NOT NULL,
    key_pin INT,
    floor INT NOT NULL,
    status ENUM('VACANT', 'OCCUPIED', 'CLEANING') DEFAULT 'VACANT'
);

-- Booking table
CREATE TABLE IF NOT EXISTS booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    guest_id INT NOT NULL,  
    room_id VARCHAR(5),  
    floor INT,           
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    room_type ENUM('Single', 'Family', 'PresidentialSuite') NOT NULL,  
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (guest_id) REFERENCES guest(guest_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE SET NULL
);

-- Create the 'keycard' table
CREATE TABLE IF NOT EXISTS keycard (
    keycard_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE, 
    guest_id INT NOT NULL, 
    room_id VARCHAR(5) NOT NULL,
    key_pin INT(6) UNIQUE NULL,  
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    expires_at TIMESTAMP NULL, 
    FOREIGN KEY (booking_id) REFERENCES booking(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (guest_id) REFERENCES guest(guest_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS housekeeper (
    housekeeper_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    floor INT NOT NULL,
    FOREIGN KEY (floor) REFERENCES room(floor)
);

-- Roster table
CREATE TABLE IF NOT EXISTS roster (
    date DATE NOT NULL,
    floor INT NOT NULL,
    room_id VARCHAR(5) NOT NULL,
    housekeeper_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (date, room_id, floor),
    FOREIGN KEY (room_id) REFERENCES room(room_id)
);

-- Price table
CREATE TABLE IF NOT EXISTS price (
    room_id VARCHAR(5) PRIMARY KEY NOT NULL,
    floor INT NOT NULL,
    room_type ENUM('Single', 'Family', 'PresidentialSuite') NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Insert data into guest
INSERT INTO guest (name, email, contact) VALUES
('Michael Davis', 'michael@example.com', '1234567890'),
('Emily Garcia', 'emily@example.com', '1235557891'),
('Jack Lee', 'jack@example.com', '1236667892'),
('Olivia Martinez', 'olivia@example.com', '1237777893'),
('Lucas Anderson', 'lucas@example.com', '1238887894'),
('Sophia Wilson', 'sophia@example.com', '1239997895'),
('Mason Scott', 'mason@example.com', '1230007896'),
('Isabella Harris', 'isabella@example.com', '1231117897'),
('Liam Clark', 'liam@example.com', '1232227898'),
('Ella Young', 'ella@example.com', '1233337899');

-- Insert data into housekeeper
INSERT INTO housekeeper (housekeeper_id, name, floor) VALUES
(1, 'John Smith', 1),
(2, 'Sarah Johnson', 1),
(3, 'Michael White', 2),
(4, 'Linda Green', 2),
(5, 'David Black', 2);

-- Insert data into room
INSERT INTO room (room_id, room_type, key_pin, floor, status) VALUES
('101', 'Single', 123456, 1, 'OCCUPIED'),
('102', 'Family', 654321, 1, 'OCCUPIED'),
('201', 'PresidentialSuite', NULL, 2, 'VACANT'),
('202', 'Single', NULL, 2, 'VACANT'),
('203', 'Family', NULL, 2, 'VACANT'),
('204', 'PresidentialSuite', NULL, 2, 'VACANT'),
('301', 'Single', NULL, 3, 'VACANT'),
('302', 'Family', NULL, 3, 'VACANT'),
('401', 'PresidentialSuite', NULL, 4, 'VACANT'),
('402', 'Single', NULL, 4, 'VACANT');

-- Insert data into booking
INSERT INTO booking (guest_id, room_id, floor, check_in, check_out, room_type, price) VALUES
(1, '101', 1, '2025-04-03', '2025-04-05', 'Single', 100.00),
(2, '102', 1, '2025-04-04', '2025-04-06', 'Family', 200.00),
(3, NULL, NULL, '2025-04-05', '2025-04-07', 'PresidentialSuite', 500.00),
(4, NULL, NULL, '2025-04-06', '2025-04-08', 'Single', 100.00),
(5, NULL, NULL, '2025-04-07', '2025-04-09', 'Family', 200.00),
(6, NULL, NULL, '2025-04-08', '2025-04-10', 'PresidentialSuite', 500.00),
(7, NULL, NULL, '2025-04-09', '2025-04-11', 'Single', 100.00),
(8, NULL, NULL, '2025-04-10', '2025-04-12', 'Family', 200.00),
(9, NULL, NULL, '2025-04-11', '2025-04-13', 'PresidentialSuite', 500.00),
(10, NULL, NULL, '2025-04-12', '2025-04-14', 'Single', 100.00);

-- Inserting data into 'keycard' table
INSERT INTO keycard (booking_id, guest_id, room_id, key_pin, issued_at, expires_at) VALUES
(1, 1, '101', 123456, '2025-04-03 10:00:00', '2025-04-06 10:00:00'),
(2, 2, '102', 654321, '2025-04-04 10:00:00', '2025-04-07 10:00:00');

-- Insert data into roster
INSERT INTO roster (date, floor, room_id, housekeeper_id, name, completed) VALUES
('2025-04-01', 1, '101', 1, 'John Smith', FALSE),
('2025-04-02', 1, '102', 2, 'Sarah Johnson', FALSE),
('2025-04-03', 2, '201', 3, 'Michael White', FALSE),
('2025-04-04', 2, '202', 4, 'Linda Green', FALSE),
('2025-04-05', 2, '203', 5, 'David Black', FALSE),
('2025-04-06', 2, '204', 6, 'Emily Brown', FALSE),
('2025-04-07', 3, '301', 7, 'Daniel Harris', FALSE),
('2025-04-08', 3, '302', 8, 'Isabella Lewis', FALSE),
('2025-04-09', 4, '401', 9, 'George Young', FALSE),
('2025-04-10', 4, '402', 10, 'Oliver Clark', FALSE);

-- Insert data into price
INSERT INTO price (room_id, floor, room_type, price) VALUES
('101', 1, 'Single', 100.00),
('102', 1, 'Family', 200.00),
('103', 1, 'PresidentialSuite', 500.00),
('201', 2, 'PresidentialSuite', 500.00),
('202', 2, 'Single', 100.00),
('203', 2, 'Family', 200.00),
('204', 2, 'PresidentialSuite', 500.00),
('301', 3, 'Single', 100.00),
('302', 3, 'Family', 200.00),
('401', 4, 'PresidentialSuite', 500.00),
('402', 4, 'Single', 100.00);