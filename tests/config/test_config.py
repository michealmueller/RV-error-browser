"""Test configuration for the application."""

import os
from pathlib import Path

# Test database configuration
TEST_DB_CONFIG = {
    'dbname': 'quantumops_test',
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': 'postgres',
    'table': 'test_table'
}

# Test Azure configuration
TEST_AZURE_CONFIG = {
    'tenant_id': 'test-tenant',
    'client_id': 'test-client',
    'client_secret': 'test-secret',
    'storage_account': 'teststorage',
    'storage_container': 'testcontainer'
}

# Test paths
TEST_DATA_DIR = Path(__file__).parent.parent / 'data'
TEST_LOG_DIR = TEST_DATA_DIR / 'logs'
TEST_UPLOAD_DIR = TEST_DATA_DIR / 'uploads'

# Create test directories if they don't exist
for directory in [TEST_DATA_DIR, TEST_LOG_DIR, TEST_UPLOAD_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Test environment variables
TEST_ENV_VARS = {
    # Database configuration
    'TEST_DB_HOST': TEST_DB_CONFIG['host'],
    'TEST_DB_PORT': TEST_DB_CONFIG['port'],
    'TEST_DB_NAME': TEST_DB_CONFIG['dbname'],
    'TEST_DB_USER': TEST_DB_CONFIG['user'],
    'TEST_DB_PASSWORD': TEST_DB_CONFIG['password'],
    'TEST_DB_TABLE': TEST_DB_CONFIG['table'],
    
    # Azure configuration
    'AZURE_TENANT_ID': TEST_AZURE_CONFIG['tenant_id'],
    'AZURE_CLIENT_ID': TEST_AZURE_CONFIG['client_id'],
    'AZURE_CLIENT_SECRET': TEST_AZURE_CONFIG['client_secret'],
    'AZURE_STORAGE_ACCOUNT': TEST_AZURE_CONFIG['storage_account'],
    'AZURE_STORAGE_CONTAINER': TEST_AZURE_CONFIG['storage_container'],
    
    # Application configuration
    'DB_CONNECTIONS': str([TEST_DB_CONFIG])
}

def setup_test_environment():
    """Set up the test environment with necessary variables and backup existing values."""
    # Store original environment variables
    original_env = {}
    for key in TEST_ENV_VARS:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    # Set test environment variables
    for key, value in TEST_ENV_VARS.items():
        os.environ[key] = value
    
    # Store original environment for cleanup
    os.environ['_TEST_ORIGINAL_ENV'] = str(original_env)

def teardown_test_environment():
    """Clean up test environment variables and restore original values."""
    try:
        # Restore original environment variables
        original_env = eval(os.environ.get('_TEST_ORIGINAL_ENV', '{}'))
        for key in TEST_ENV_VARS:
            if key in os.environ:
                del os.environ[key]
            if key in original_env:
                os.environ[key] = original_env[key]
        
        # Clean up test directories
        for directory in [TEST_DATA_DIR, TEST_LOG_DIR, TEST_UPLOAD_DIR]:
            if directory.exists():
                for file in directory.glob('*'):
                    try:
                        if file.is_file():
                            file.unlink()
                    except Exception:
                        pass  # Ignore cleanup errors
        
        # Remove the original environment marker
        if '_TEST_ORIGINAL_ENV' in os.environ:
            del os.environ['_TEST_ORIGINAL_ENV']
    except Exception:
        pass  # Ensure cleanup doesn't raise exceptions 