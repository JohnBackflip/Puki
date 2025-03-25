# services/user/database.py
import os
import mysql.connector
from mysql.connector import pooling

# Database configuration
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "user_service"),
    "password": os.getenv("MYSQL_PASSWORD", "your_password_here"),
    "database": os.getenv("MYSQL_DATABASE", "user_db"),
    "pool_name": "user_pool",
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

def init_db():
    """Initialize database tables"""
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Create roles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create user_roles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INT NOT NULL,
            role_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, role_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
        )
    """)
    
    # Insert default roles if they don't exist
    cursor.execute("""
        INSERT IGNORE INTO roles (name) VALUES 
        ('admin'), ('staff'), ('guest')
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

def run_migrations():
    """Run database migrations"""
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    
    # Create migrations table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            version VARCHAR(50) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Get applied migrations
    cursor.execute("SELECT version FROM migrations")
    applied = {row[0] for row in cursor.fetchall()}
    
    # Define migrations
    migrations = [
        ("001_initial", init_db),
        # Add more migrations here as needed
    ]
    
    # Run pending migrations
    for version, migrate in migrations:
        if version not in applied:
            migrate()
            cursor.execute(
                "INSERT INTO migrations (version) VALUES (%s)",
                (version,)
            )
            conn.commit()
    
    cursor.close()
    conn.close()