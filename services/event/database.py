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
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            # Create events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    event_type VARCHAR(50) NOT NULL,
                    start_date DATETIME NOT NULL,
                    end_date DATETIME NOT NULL,
                    location VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Create price adjustments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_adjustments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    event_id INT NOT NULL,
                    adjustment_type ENUM('percentage', 'fixed') NOT NULL,
                    value DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)
            
            connection.commit()
    except pymysql.Error as e:
        print(f"Error initializing database: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def run_migrations():
    """Run database migrations"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            # Add any necessary migrations here
            pass
        connection.commit()
    except pymysql.Error as e:
        print(f"Error running migrations: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close() 