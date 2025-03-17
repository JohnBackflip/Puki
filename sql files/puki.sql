-- js run this file 

CREATE DATABASE IF NOT EXISTS PUKI;
USE puki;

-- DROP DATABASE IF EXISTS puki;
-- DROP TABLE IF EXISTS keycard;
-- DROP TABLE IF EXISTS booking;
-- DROP TABLE IF EXISTS customer;
-- DROP TABLE IF EXISTS `user`;


CREATE TABLE `user` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  `email` VARCHAR(128) UNIQUE NOT NULL,
  `password_hash` VARCHAR(256) NOT NULL,
  `role` ENUM('admin', 'staff') NOT NULL,
  PRIMARY KEY (`user_id`)
);


CREATE TABLE customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    address VARCHAR(255) NOT NULL,
    contact VARCHAR(15) NOT NULL,
    email VARCHAR(128) UNIQUE NOT NULL,
    nationality VARCHAR(64) NOT NULL,
    verified BOOLEAN DEFAULT FALSE, 
    otp VARCHAR(6) NULL,  
    otp_expiry DATETIME NULL  
);



CREATE TABLE booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,  -- Staff who created the booking
    customer_id INT NOT NULL,  -- The actual customer staying in the hotel
    room_id VARCHAR(36) NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    status ENUM('CONFIRMED', 'CANCELLED', 'CHECKED-IN', 'CHECKED-OUT') DEFAULT 'CONFIRMED',
    FOREIGN KEY (user_id) REFERENCES `user`(user_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE
);

CREATE TABLE keycard (
    keycard_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE, 
    user_id INT NULL, 
    customer_id INT NOT NULL, 
    room_id VARCHAR(36) NOT NULL,
    key_pin VARCHAR(6) NOT NULL,  
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,  
	FOREIGN KEY (booking_id) REFERENCES booking(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE
);
