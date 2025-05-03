import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
import os
import tempfile
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance."""
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
        yield app
        app.quit()
    else:
        yield QApplication.instance()

@pytest.fixture
def temp_settings():
    """Create temporary settings for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        settings_path = tmp.name
    settings = QSettings(settings_path, QSettings.IniFormat)
    yield settings
    settings.sync()
    os.unlink(settings_path)

@pytest.fixture
def mock_connection():
    """Create a mock database connection."""
    return {
        "name": "test_connection",
        "host": "localhost",
        "port": "5432",
        "database": "test_db",
        "username": "test_user",
        "password": "test_pass",
        "default_table": "test_table"
    }

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "unit: mark test as unit test"
    )

@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    """Set up test environment variables."""
    # Set test-specific environment variables
    monkeypatch.setenv('TESTING', 'true')
    monkeypatch.setenv('PYTHONPATH', os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 