import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Load environment variables
if os.getenv("TESTING"):
    load_dotenv(".env.test")
else:
    load_dotenv()

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "payment_service"),
    "password": os.getenv("DB_PASSWORD", "payment_service_password"),
    "database": os.getenv("DB_NAME", "payment_service"),
    "pool_name": "payment_service_pool",
    "pool_size": 5
}

# Global connection pool
is_testing = os.getenv("TESTING") == "true"
connection_pool = None if is_testing else mysql.connector.pooling.MySQLConnectionPool(**db_config)

def get_db():
    """Get a database connection from the pool"""
    if is_testing:
        import sys
        from pathlib import Path
        testing_dir = str(Path(__file__).parent.parent.parent / "testing")
        if testing_dir not in sys.path:
            sys.path.append(testing_dir)
        from conftest import mock_cursor_instance
        return mock_cursor_instance
    return connection_pool.get_connection().cursor(dictionary=True)

def init_db():
    """Initialize the database"""
    if is_testing:
        return
    
    connection = mysql.connector.connect(
        host=db_config["host"],
        port=db_config["port"],
        user=db_config["user"],
        password=db_config["password"]
    )
    cursor = connection.cursor()
    
    # Create database if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
    cursor.execute(f"USE {db_config['database']}")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',
            status ENUM('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED') NOT NULL DEFAULT 'PENDING',
            payment_method ENUM('CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER') NOT NULL,
            transaction_id VARCHAR(255),
            payment_details JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_booking (booking_id),
            INDEX idx_status (status)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            id INT AUTO_INCREMENT PRIMARY KEY,
            payment_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            reason TEXT,
            status ENUM('PENDING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (payment_id) REFERENCES payments(id),
            INDEX idx_payment (payment_id),
            INDEX idx_status (status)
        )
    """)
    
    connection.commit()
    cursor.close()
    connection.close()

def run_migrations():
    """Run database migrations"""
    if is_testing:
        return
    
    # Add any migrations here
    pass 