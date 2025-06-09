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
from .db_config import DB_CONFIG
import os
import tempfile
import sys
from tests.config.test_config import setup_test_environment, teardown_test_environment

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance with proper lifecycle management."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        app.setQuitOnLastWindowClosed(True)
    
    # Ensure we're in a clean state
    for widget in app.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    app.processEvents()
    
    yield app
    
    # Clean up before quitting
    for widget in app.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    app.processEvents()
    
    # Only quit if we created the instance
    if QApplication.instance() is app:
        app.quit()
        app.processEvents()

@pytest.fixture
def qtbot(qt_app):
    """Create a QtBot instance."""
    from pytestqt.qtbot import QtBot
    return QtBot(qt_app)

@pytest.fixture(autouse=True)
def cleanup_qt_windows(qt_app):
    """Clean up any Qt windows after each test with improved resource management."""
    yield
    # Close and delete all top-level windows
    for widget in qt_app.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    # Process any pending events
    qt_app.processEvents()
    # Force garbage collection of deleted widgets
    qt_app.sendPostedEvents(None, 0)
    # Ensure all events are processed
    qt_app.processEvents()

@pytest.fixture(scope="session")
def test_db():
    """Create and clean up test database with proper isolation."""
    create_test_database()
    try:
        yield get_test_db_config()
    finally:
        cleanup_test_database()

@pytest.fixture
def db(test_db):
    """Create a database instance with transaction management."""
    db = Database(test_db)
    # Start a transaction
    db.begin_transaction()
    try:
        yield db
    finally:
        # Rollback the transaction to ensure test isolation
        db.rollback()
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
        "host": DB_CONFIG['host'],
        "port": DB_CONFIG['port'],
        "database": DB_CONFIG['database'],
        "username": DB_CONFIG['username'],
        "password": DB_CONFIG['password'],
        "default_table": DB_CONFIG['default_table']
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

@pytest.fixture(autouse=True)
def setup_teardown():
    """Set up and tear down the test environment for each test with proper cleanup."""
    setup_test_environment()
    try:
        yield
    finally:
        teardown_test_environment() 