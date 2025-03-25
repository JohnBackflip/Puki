# housekeeping/database.py
import os
import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
from contextlib import contextmanager

# Database configuration
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "root"),
    "database": os.getenv("MYSQL_DATABASE", "hotel"),
    "port": int(os.getenv("MYSQL_PORT", 3306))
}

# Connection pool configuration
POOL_CONFIG = {
    "pool_name": "housekeeping_pool",
    "pool_size": 5,
    **DB_CONFIG
}

# Initialize the connection pool
try:
    connection_pool = MySQLConnectionPool(**POOL_CONFIG)
except Error as e:
    print(f"Error connecting to MySQL: {e}")
    raise

def init_db():
    """Initialize the database and create tables if they don't exist."""
    from . import models
    
    with get_db() as cursor:
        models.CleaningTask.create_table(cursor)

def run_migrations():
    """Run any necessary database migrations."""
    with get_db() as cursor:
        # Add any migrations here
        pass

@contextmanager
def get_db():
    """Get a database connection from the pool."""
    conn = connection_pool.get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        yield cursor
        conn.commit()
    except Error as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()