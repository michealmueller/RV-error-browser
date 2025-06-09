"""Test utilities."""
import os
import time
import psycopg2
from pathlib import Path
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from .db_config import DB_CONFIG, TEST_TABLE_SCHEMA
from typing import Dict, Any

def wait_for_postgres(max_retries=5, retry_interval=1):
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
        user="postgres",
        password="postgres",
        host="localhost"
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Create test database if it doesn't exist
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'quantumops_test'")
            if not cur.fetchone():
                cur.execute("CREATE DATABASE quantumops_test")
    finally:
        conn.close()
    
    # Connect to test database
    test_conn = psycopg2.connect(
        dbname="quantumops_test",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    
    try:
        with test_conn.cursor() as cur:
            # Create test tables
            cur.execute("""
                CREATE TABLE IF NOT EXISTS builds (
                    id SERIAL PRIMARY KEY,
                    build_id VARCHAR(255) NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    version VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id SERIAL PRIMARY KEY,
                    build_id VARCHAR(255) NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    version VARCHAR(50) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    finally:
        test_conn.close()

def cleanup_test_database():
    """Clean up test database."""
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Drop test database
            cur.execute("DROP DATABASE IF EXISTS quantumops_test")
    finally:
        conn.close()

def get_test_db_config():
    """Get test database configuration."""
    return {
        "dbname": "quantumops_test",
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