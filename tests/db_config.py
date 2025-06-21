"""Test database configuration."""
import os

# Database connection settings
DB_CONFIG = {
    "host": os.getenv("TEST_DB_HOST", "localhost"),
    "port": os.getenv("TEST_DB_PORT", "5432"),
    "database": os.getenv("TEST_DB_NAME", "test_db"),
    "username": os.getenv("TEST_DB_USER", "postgres"),
    "password": os.getenv("TEST_DB_PASSWORD", "postgres"),
    "default_table": os.getenv("TEST_DB_TABLE", "test_table"),
}

# Test table schema
TEST_TABLE_SCHEMA = """
    CREATE TABLE IF NOT EXISTS test_table (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        level VARCHAR(10),
        message TEXT
    )
"""
