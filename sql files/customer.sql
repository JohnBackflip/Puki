CREATE TABLE customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    passport_nric VARCHAR(20) UNIQUE NOT NULL,
    address VARCHAR(255) NOT NULL,
    contact VARCHAR(15) NOT NULL,
    email VARCHAR(128) UNIQUE NOT NULL,
    nationality VARCHAR(64) NOT NULL
);