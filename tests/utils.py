"""Test utilities."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from .db_config import DB_CONFIG, TEST_TABLE_SCHEMA

def create_test_database():
    """Create a test database."""
    # Connect to default postgres database
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    # Create test database
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
    cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
    cur.close()
    conn.close()
    
    # Connect to test database and create test table
    test_conn = psycopg2.connect(
        dbname=DB_CONFIG['database'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port']
    )
    cur = test_conn.cursor()
    cur.execute(TEST_TABLE_SCHEMA)
    test_conn.commit()
    cur.close()
    test_conn.close()

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