"""Test utilities."""
import os
import time
import psycopg2
from pathlib import Path
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from .db_config import DB_CONFIG, TEST_TABLE_SCHEMA, BUILDS_TABLE_SCHEMA, HISTORY_TABLE_SCHEMA
from typing import Dict, Any

def wait_for_postgres(max_retries=5, retry_interval=1):
    """Wait for PostgreSQL to be ready."""
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=DB_CONFIG['username'],
                password=DB_CONFIG['password'],
                host=DB_CONFIG['host']
            )
            conn.close()
            return
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                time.sleep(retry_interval)
            else:
                raise

def create_test_database():
    """Create a test database."""
    # Wait for PostgreSQL to be ready
    wait_for_postgres()
    
    # Connect to default database
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host']
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Drop test database if it exists
            cur.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
            # Create test database
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
    finally:
        conn.close()
    
    # Connect to test database
    test_conn = psycopg2.connect(
        dbname=DB_CONFIG['database'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host']
    )
    
    try:
        with test_conn.cursor() as cur:
            # Create test tables
            cur.execute(TEST_TABLE_SCHEMA)
            cur.execute(BUILDS_TABLE_SCHEMA)
            cur.execute(HISTORY_TABLE_SCHEMA)
    finally:
        test_conn.close()

def cleanup_test_database():
    """Clean up test database."""
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host']
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Drop test database
            cur.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
    finally:
        conn.close()

def get_test_db_config():
    """Get test database configuration."""
    return {
        "dbname": DB_CONFIG['database'],
        "user": DB_CONFIG['username'],
        "password": DB_CONFIG['password'],
        "host": DB_CONFIG['host'],
        "port": DB_CONFIG['port']
    }

def get_test_connection():
    """Get a connection to the test database."""
    return psycopg2.connect(
        dbname=DB_CONFIG['database'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port']
    ) 