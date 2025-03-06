CREATE TABLE booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,  -- Staff who created the booking
    customer_id INT NOT NULL,  -- The actual customer staying in the hotel
    room_id VARCHAR(36) NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    status ENUM('CONFIRMED', 'CANCELLED', 'CHECKED-IN', 'CHECKED-OUT') DEFAULT 'CONFIRMED'
);
