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
    "user": os.getenv("DB_USER", "notification_service"),
    "password": os.getenv("DB_PASSWORD", "notification_service_password"),
    "database": os.getenv("DB_NAME", "notification_service"),
    "pool_name": "notification_service_pool",
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
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user (user_id),
            INDEX idx_type (type),
            INDEX idx_created_at (created_at)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type VARCHAR(50) NOT NULL,
            email_enabled BOOLEAN DEFAULT TRUE,
            push_enabled BOOLEAN DEFAULT TRUE,
            sms_enabled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_type (user_id, type),
            INDEX idx_user (user_id)
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