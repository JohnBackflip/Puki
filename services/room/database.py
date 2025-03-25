# room/database.py
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
    "user": os.getenv("DB_USER", "room_service"),
    "password": os.getenv("DB_PASSWORD", "room_service_password"),
    "database": os.getenv("DB_NAME", "room_service"),
    "pool_name": "room_service_pool",
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
        CREATE TABLE IF NOT EXISTS rooms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_number VARCHAR(10) NOT NULL UNIQUE,
            room_type ENUM('SINGLE', 'DOUBLE', 'SUITE') NOT NULL,
            price_per_night DECIMAL(10,2) NOT NULL,
            floor INT NOT NULL,
            status ENUM('AVAILABLE', 'OCCUPIED', 'MAINTENANCE') NOT NULL DEFAULT 'AVAILABLE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_availability (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            room_type ENUM('SINGLE', 'DOUBLE', 'SUITE') NOT NULL,
            available_count INT NOT NULL,
            base_price DECIMAL(10,2) NOT NULL,
            UNIQUE KEY date_room_type_idx (date, room_type)
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