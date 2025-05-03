"""Test utilities."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from .db_config import DB_CONFIG, TEST_TABLE_SCHEMA
import time
from typing import Dict, Any

def wait_for_postgres(max_retries: int = 5, delay: int = 2) -> None:
    """Wait for PostgreSQL to be ready."""
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="postgres",
                host="localhost"
            )
            conn.close()
            return
        except psycopg2.OperationalError:
            if i == max_retries - 1:
                raise
            time.sleep(delay)

def create_test_database() -> Dict[str, Any]:
    """Create a test database and return connection info."""
    wait_for_postgres()
    
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute("DROP DATABASE IF EXISTS test_db")
    cursor.execute("CREATE DATABASE test_db")
    cursor.close()
    conn.close()
    
    return {
        "dbname": "test_db",
        "user": "postgres",
        "password": "postgres",
        "host": "localhost"
    }

def drop_test_database():
    """Drop the test database."""
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
    cur.close()
    conn.close()

def get_test_connection():
    """Get a connection to the test database."""
    return psycopg2.connect(
        dbname=DB_CONFIG['database'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port']
    ) 