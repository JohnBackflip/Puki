# staff/database.py
import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

# MySQL connection pool configuration
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "hotel_db"),
    "pool_name": "mypool",
    "pool_size": 5
}

# Create connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def get_db():
    """Get a database connection from the pool"""
    if os.getenv("TESTING") == "true":
        return None  # Return None for testing
    return connection_pool.get_connection()

def init_db():
    """Initialize the database with required tables"""
    if os.getenv("TESTING") == "true":
        return  # Skip initialization for testing
        
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    
    try:
        # Create staff table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                role VARCHAR(50) NOT NULL,
                department VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Create staff_schedule table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_schedule (
                id INT AUTO_INCREMENT PRIMARY KEY,
                staff_id INT NOT NULL,
                shift_start TIMESTAMP NOT NULL,
                shift_end TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id)
            )
        """)
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def run_migrations():
    """Run any pending database migrations"""
    if os.getenv("TESTING") == "true":
        return  # Skip migrations for testing
        
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    
    try:
        # Add any new migrations here
        # Example:
        # cursor.execute("ALTER TABLE staff ADD COLUMN phone VARCHAR(20)")
        conn.commit()
    finally:
        cursor.close()
        conn.close()