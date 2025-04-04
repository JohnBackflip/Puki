DROP DATABASE IF EXISTS puki;
CREATE DATABASE IF NOT EXISTS puki;
USE puki;

-- Create the 'guest' table
CREATE TABLE IF NOT EXISTS guest (
  guest_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  email VARCHAR(128) UNIQUE NOT NULL,
  phone_number varchar(10) UNIQUE NOT NULL
);

-- Now create the 'booking' table which references 'guest'
CREATE TABLE IF NOT EXISTS booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    guest_id INT NOT NULL,  
    room_id VARCHAR(36) NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    room_type ENUM('Single','Family', 'PresidentialSuite') NOT NULL,  
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (guest_id) REFERENCES guest(guest_id) ON DELETE CASCADE
);

-- Create the 'room' table 
CREATE TABLE IF NOT EXISTS room (
    room_id VARCHAR(36) PRIMARY KEY, 
    room_type ENUM('Single', 'Family', 'PresidentialSuite') NOT NULL,
    status ENUM('VACANT', 'OCCUPIED', 'CLEANING') DEFAULT 'VACANT'
);

-- Create the 'keycard' table
CREATE TABLE IF NOT EXISTS keycard (
    keycard_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE, 
    guest_id INT NOT NULL, 
    room_id VARCHAR(36) NOT NULL,
    key_pin VARCHAR(6) NOT NULL,  
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    expires_at TIMESTAMP NULL, 
    FOREIGN KEY (booking_id) REFERENCES booking(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (guest_id) REFERENCES guest(guest_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE CASCADE
);

-- Create the 'housekeeper' table
CREATE TABLE IF NOT EXISTS housekeeper (
    housekeeper_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL
);

-- Create the 'roster' table
CREATE TABLE IF NOT EXISTS roster (
    date DATE NOT NULL,
    floor INT,
    room_id VARCHAR(36),
    housekeeper_id INT,
    completed BOOLEAN DEFAULT false,
    PRIMARY KEY (date, room_id, floor), -- composite primary key
    FOREIGN KEY (housekeeper_id) REFERENCES housekeeper(housekeeper_id),
    FOREIGN KEY (room_id) REFERENCES room(room_id)
);

-- Create the 'price' table
CREATE TABLE IF NOT EXISTS price (
    room_type ENUM('Single', 'Family', 'PresidentialSuite') NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Inserting data into 'guest' table
INSERT INTO guest (name, email, phone_number) VALUES
('Michael Davis', 'michael@example.com', 1234567890),
('Emily Garcia', 'emily@example.com', 1235557891),
('Jack Lee', 'jack@example.com', 1236667892),
('Olivia Martinez', 'olivia@example.com', 1237777893),
('Lucas Anderson', 'lucas@example.com', 1238887894),
('Sophia Wilson', 'sophia@example.com', 1239997895),
('Mason Scott', 'mason@example.com', 1230007896),
('Isabella Harris', 'isabella@example.com', 1231117897),
('Liam Clark', 'liam@example.com', 1232227898),
('Ella Young', 'ella@example.com', 1233337899);

-- Inserting data into 'booking' table
INSERT INTO booking (guest_id, room_id, check_in, check_out, room_type, price) VALUES
(1, 'room001', '2025-05-01', '2025-05-05', 'Single', 100.00),
(2, 'room002', '2025-05-02', '2025-05-06', 'Family', 200.00),
(3, 'room003', '2025-05-03', '2025-05-07', 'PresidentialSuite', 500.00),
(4, 'room004', '2025-05-04', '2025-05-08', 'Single', 100.00),
(5, 'room005', '2025-05-05', '2025-05-09', 'Family', 200.00),
(6, 'room006', '2025-05-06', '2025-05-10', 'PresidentialSuite', 500.00),
(7, 'room007', '2025-05-07', '2025-05-11', 'Single', 100.00),
(8, 'room008', '2025-05-08', '2025-05-12', 'Family', 200.00),
(9, 'room009', '2025-05-09', '2025-05-13', 'PresidentialSuite', 500.00),
(10, 'room010', '2025-05-10', '2025-05-14', 'Single', 100.00);

-- Inserting data into 'room' table
INSERT INTO room (room_id, room_type, status) VALUES
('room001', 'Single', 'VACANT'),
('room002', 'Family', 'OCCUPIED'),
('room003', 'PresidentialSuite', 'VACANT'),
('room004', 'Single', 'OCCUPIED'),
('room005', 'Family', 'VACANT'),
('room006', 'PresidentialSuite', 'OCCUPIED'),
('room007', 'Single', 'VACANT'),
('room008', 'Family', 'OCCUPIED'),
('room009', 'PresidentialSuite', 'VACANT'),
('room010', 'Single',  'VACANT');

-- Inserting data into 'keycard' table
INSERT INTO keycard (booking_id, guest_id, room_id, key_pin, issued_at, expires_at) VALUES
(1, 1, 'room001', '123456', '2025-05-01 10:00:00', '2025-05-05 10:00:00'),
(2, 2, 'room002', '654321', '2025-05-02 10:00:00', '2025-05-06 10:00:00'),
(3, 3, 'room003', '112233', '2025-05-03 10:00:00', '2025-05-07 10:00:00'),
(4, 4, 'room004', '445566', '2025-05-04 10:00:00', '2025-05-08 10:00:00'),
(5, 5, 'room005', '789012', '2025-05-05 10:00:00', '2025-05-09 10:00:00'),
(6, 6, 'room006', '345678', '2025-05-06 10:00:00', '2025-05-10 10:00:00'),
(7, 7, 'room007', '987654', '2025-05-07 10:00:00', '2025-05-11 10:00:00'),
(8, 8, 'room008', '567890', '2025-05-08 10:00:00', '2025-05-12 10:00:00'),
(9, 9, 'room009', '135791', '2025-05-09 10:00:00', '2025-05-13 10:00:00'),
(10, 10, 'room010', '246810', '2025-05-10 10:00:00', '2025-05-14 10:00:00');

-- Inserting data into 'housekeeper' table
INSERT INTO housekeeper (name) VALUES
('John Smith'),
('Sarah Johnson'),
('Michael White'),
('Linda Green'),
('David Black'),
('Emily Brown'),
('Daniel Harris'),
('Isabella Lewis'),
('George Young'),
('Oliver Clark');

-- Inserting data into 'roster' table
INSERT INTO roster (date, floor, room_id, housekeeper_id) VALUES
('2025-05-01',1, 'room001', 1),
('2025-05-02', 2, 'room002', 2),
('2025-05-03', 3, 'room003', 3),
('2025-05-04', 4, 'room004', 4),
('2025-05-05', 5, 'room005', 5),
('2025-05-06', 6, 'room006', 6),
('2025-05-07', 7, 'room007', 7),
('2025-05-08', 8, 'room008', 8),
('2025-05-09', 9, 'room009', 9),
('2025-05-10', 10, 'room010', 10);

-- Inserting data into 'price' table
INSERT INTO price (room_type, price) VALUES
('Single', 100.00),
('Family', 200.00),
('PresidentialSuite', 500.00);
