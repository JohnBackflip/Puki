import os
import mysql.connector
from mysql.connector import pooling

# Database configuration
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "password"),
    "database": os.getenv("MYSQL_DATABASE", "feedback_db"),
    "pool_name": "feedback_pool",
    "pool_size": 5
}

# Create connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def get_db():
    """Get database connection from pool"""
    try:
        connection = connection_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        yield cursor
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Initialize database and tables
def init_db():
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    
    # Create reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT NOT NULL,
            user_id INT NOT NULL,
            rating ENUM('ONE', 'TWO', 'THREE', 'FOUR', 'FIVE') NOT NULL,
            comment TEXT,
            status ENUM('PENDING', 'RESPONDED', 'ARCHIVED') DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Create responses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            review_id INT NOT NULL,
            staff_id INT NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES reviews(id)
        )
    """)
    
    # Create review_metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            review_id INT NOT NULL,
            sentiment_score FLOAT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES reviews(id)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()