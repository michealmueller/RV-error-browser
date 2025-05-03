import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from app import DatabaseApp

@pytest.fixture
def app(qtbot):
    """Create the application window."""
    window = DatabaseApp()
    qtbot.addWidget(window)
    return window

def test_app_initialization(app):
    """Test that the application initializes correctly."""
    assert app.windowTitle() == "PostgreSQL Viewer"
    assert app.connection_combo.count() == 0
    assert app.host_input.text() == ""
    assert app.port_input.text() == "5432"
    assert app.database_input.text() == ""
    assert app.username_input.text() == ""
    assert app.password_input.text() == ""
    assert app.table_input.text() == ""

def test_connection_management(app, qtbot):
    """Test connection management functionality."""
    # Add a connection
    app.add_connection()
    assert app.connection_combo.count() == 1
    
    # Select the connection
    app.connection_combo.setCurrentIndex(0)
    assert app.connection_combo.currentText() == "New Connection"
    
    # Clear connections
    app.clear_connections()
    assert app.connection_combo.count() == 0

def test_log_messages(app):
    """Test log message functionality."""
    # Add info message
    app.log_message("Test info message", "INFO")
    assert "Test info message" in app.log_output.toPlainText()
    
    # Add error message
    app.log_message("Test error message", "ERROR")
    assert "Test error message" in app.log_output.toPlainText()
    
    # Clear log
    app.clear_log()
    assert app.log_output.toPlainText() == ""

def test_query_results(app):
    """Test query results functionality."""
    # Set query results
    app.set_query_results([("id", "timestamp", "level", "message")], 
                         [(1, "2024-01-01", "INFO", "Test message")])
    assert app.results_table.rowCount() == 1
    assert app.results_table.columnCount() == 4
    
    # Clear results
    app.clear_results()
    assert app.results_table.rowCount() == 0
    assert app.results_table.columnCount() == 0 