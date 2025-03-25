# booking/database.py
import os
import pymysql
from pymysql.cursors import DictCursor

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),  # Updated default password
    "database": os.getenv("DB_NAME", "hotel"),
    "cursorclass": DictCursor,
    "autocommit": False  # Explicitly set autocommit to False for transaction support
}

# Test mode flag
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

def get_db():
    """Get a database connection."""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def init_db():
    """Initialize the database"""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            # Create rooms table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    room_number VARCHAR(10) NOT NULL UNIQUE,
                    room_type ENUM('standard', 'deluxe', 'suite') NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    capacity INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Create bookings table with customer_id field
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    customer_id INT NOT NULL,
                    room_id INT NOT NULL,
                    check_in_date DATE NOT NULL,
                    check_out_date DATE NOT NULL,
                    status ENUM('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled') NOT NULL DEFAULT 'pending',
                    total_price DECIMAL(10, 2) NOT NULL,
                    special_requests TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES rooms(id)
                    -- Optionally, if a customers table exists, add:
                    -- , FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                )
            """)

            
            # Create booking_payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS booking_payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    payment_method VARCHAR(50) NOT NULL,
                    transaction_id VARCHAR(100),
                    status ENUM('pending', 'paid', 'refunded', 'failed') NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (booking_id) REFERENCES bookings(id)
                )
            """)
        connection.commit()
    finally:
        connection.close()

def run_migrations():
    """Run any necessary database migrations."""
    if TEST_MODE:
        return
    # Add any migrations here
    pass
