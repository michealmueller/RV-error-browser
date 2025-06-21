"""Constants for QuantumOps application."""
import os

# Azure configuration constants
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "")

# Database connections configuration
DB_CONNECTIONS = [
    {
        "name": "Default Connection",
        "host": "localhost",
        "port": "5432",
        "dbname": "postgres",
        "user": "postgres",
        "password": "",
    }
]
