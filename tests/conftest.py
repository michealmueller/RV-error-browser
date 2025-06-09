import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, Qt
from unittest.mock import MagicMock, patch
from quantumops.views.main_window import MainWindow
from quantumops.views.azure_config_dialog import AzureConfigDialog
from quantumops.services.azure_service import AzureService
from quantumops.models.build_manager import BuildManager
from quantumops.controllers.build_controller import BuildController
from quantumops.models.database import Database
from .utils import create_test_database, cleanup_test_database, get_test_db_config
import os
import tempfile
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture(scope="session")
def test_db():
    """Create and clean up test database."""
    create_test_database()
    yield get_test_db_config()
    cleanup_test_database()

@pytest.fixture
def db(test_db):
    """Create a database instance."""
    db = Database(test_db)
    yield db
    db.close()

@pytest.fixture
def mock_azure_service():
    """Create a mock Azure service."""
    service = MagicMock(spec=AzureService)
    service.initialize.return_value = True
    service.upload_file.return_value = True
    service.download_file.return_value = True
    service.delete_file.return_value = True
    return service

@pytest.fixture
def build_manager(mock_azure_service, tmp_path):
    """Create a build manager instance."""
    manager = BuildManager()
    manager._azure_service = mock_azure_service
    manager._download_dir = tmp_path
    return manager

@pytest.fixture
def build_controller(build_manager, db):
    """Create a build controller instance."""
    return BuildController(build_manager, db)

@pytest.fixture
def main_window(app, build_controller):
    """Create a main window instance."""
    window = MainWindow(["test-app"])
    window._build_controller = build_controller
    return window

@pytest.fixture
def azure_config_dialog(app):
    """Create an Azure config dialog instance."""
    return AzureConfigDialog()

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