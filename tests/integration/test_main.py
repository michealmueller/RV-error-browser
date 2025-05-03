import pytest
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer
from app import DatabaseApp
from ..utils import create_test_database, drop_test_database, get_test_connection
from ..db_config import DB_CONFIG
import os

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for testing."""
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
        # Set environment variable to indicate we're running in a test environment
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        yield app
        app.quit()
    else:
        yield QApplication.instance()

@pytest.fixture
def app(qapp):
    """Create a DatabaseApp instance for testing."""
    from app import DatabaseApp
    app = DatabaseApp()
    yield app
    app.close()

@pytest.mark.timeout(10)
def test_application_startup(app):
    """Test that the application starts up correctly."""
    assert app.isVisible()
    assert app.windowTitle() == "PostgreSQL Viewer"

@pytest.mark.timeout(30)
def test_database_connection(app, qtbot):
    """Test connecting to the database."""
    # Set connection details
    app.host_input.setText(DB_CONFIG["host"])
    app.port_input.setText(DB_CONFIG["port"])
    app.database_input.setText(DB_CONFIG["database"])
    app.username_input.setText(DB_CONFIG["username"])
    app.password_input.setText(DB_CONFIG["password"])
    app.table_input.setText(DB_CONFIG["default_table"])
    
    # Click connect button
    qtbot.mouseClick(app.connect_button, Qt.LeftButton)
    
    # Verify connection
    assert "Connected to database" in app.log_output.toPlainText()

@pytest.mark.timeout(30)
def test_query_execution(app, qtbot):
    """Test executing a query."""
    # Connect to database first
    test_database_connection(app, qtbot)
    
    # Execute query
    qtbot.mouseClick(app.query_button, Qt.LeftButton)
    
    # Verify results
    assert app.results_table.rowCount() > 0
    assert app.results_table.columnCount() > 0

@pytest.mark.timeout(20)
def test_connection_management(app, qtbot):
    """Test managing database connections."""
    # Add a connection
    app.add_connection()
    assert app.connection_combo.count() == 1
    
    # Edit the connection
    app.edit_connection()
    assert "Edit Connection" in app.log_output.toPlainText()
    
    # Delete the connection
    app.delete_connection()
    assert app.connection_combo.count() == 0

@pytest.mark.timeout(15)
def test_error_handling(app, qtbot):
    """Test error handling."""
    # Try to connect with invalid credentials
    app.host_input.setText("invalid_host")
    qtbot.mouseClick(app.connect_button, Qt.LeftButton)
    assert "Error" in app.log_output.toPlainText()
    
    # Try to execute query without connection
    qtbot.mouseClick(app.query_button, Qt.LeftButton)
    assert "Error" in app.log_output.toPlainText() 