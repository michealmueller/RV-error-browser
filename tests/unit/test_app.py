import pytest
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from app import DatabaseApp
from datetime import datetime
import psycopg2
from psycopg2 import Error

@pytest.fixture
def app(qtbot, mocker):
    """Create the application window with a clean state."""
    # Mock QSettings to prevent loading saved connections
    mock_settings = mocker.MagicMock()
    mock_settings.value.return_value = None  # Return None instead of empty list
    mocker.patch('PySide6.QtCore.QSettings', return_value=mock_settings)
    
    window = DatabaseApp()
    qtbot.addWidget(window)
    
    # Clean up after each test
    yield window
    window.connections = []
    window.update_connection_combo()

@pytest.fixture
def mock_connection(mocker):
    """Create a mock database connection."""
    mock_conn = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor

@pytest.fixture
def mock_settings(mocker):
    """Create a mock QSettings object."""
    mock_settings = mocker.MagicMock()
    mock_settings.value.return_value = None
    mocker.patch('app.QSettings', return_value=mock_settings)  # Patch at the module level
    return mock_settings

@pytest.mark.gui
def test_app_initialization(app):
    """Test that the application initializes correctly."""
    # Clear any existing connections
    app.connections = []
    app.update_connection_combo()
    
    assert app.windowTitle() == "RVEB - RosieVision Error Browser"
    assert app.connection_combo.count() == 1  # Only empty item
    assert app.host_label.text() == ""
    assert app.port_label.text() == "5432"
    assert app.dbname_label.text() == ""
    assert app.user_label.text() == ""
    assert app.password_label.text() == "********"  # Password field shows asterisks
    assert app.table_input.text() == "error_logs"
    
    # Check button states
    assert not app.connect_btn.isEnabled()
    assert not app.disconnect_btn.isEnabled()
    assert not app.query_btn.isEnabled()
    assert app.clear_log_btn.isEnabled()

@pytest.mark.gui
def test_connection_management(app, qtbot):
    """Test connection management functionality."""
    # Test empty connection selection
    app.connection_combo.setCurrentIndex(0)
    assert app.host_label.text() == ""
    assert app.port_label.text() == "5432"
    assert app.dbname_label.text() == ""
    assert app.user_label.text() == ""
    assert app.password_label.text() == "********"
    assert app.table_input.text() == "error_logs"
    assert not app.connect_btn.isEnabled()
    
    # Test adding a connection
    test_conn = {
        'name': 'Test Connection',
        'host': 'localhost',
        'port': '5432',
        'dbname': 'test_db',
        'user': 'test_user',
        'password': 'test_pass',
        'table': 'test_table'
    }
    app.connections.append(test_conn)
    app.update_connection_combo()
    
    # Test selecting the connection
    app.connection_combo.setCurrentIndex(1)
    assert app.host_label.text() == test_conn['host']
    assert app.port_label.text() == test_conn['port']
    assert app.dbname_label.text() == test_conn['dbname']
    assert app.user_label.text() == test_conn['user']
    assert app.password_label.text() == "********"
    assert app.table_input.text() == test_conn['table']
    assert app.connect_btn.isEnabled()

@pytest.mark.gui
def test_log_messages(app):
    """Test log message functionality."""
    # Test info message
    app.log_message("Test info message", "INFO")
    assert "Test info message" in app.log_window.toHtml()
    assert "INFO" in app.log_window.toHtml()
    
    # Test error message
    app.log_message("Test error message", "ERROR")
    assert "Test error message" in app.log_window.toHtml()
    assert "ERROR" in app.log_window.toHtml()
    
    # Test success message
    app.log_message("Test success message", "SUCCESS")
    assert "Test success message" in app.log_window.toHtml()
    assert "SUCCESS" in app.log_window.toHtml()
    
    # Test warning message
    app.log_message("Test warning message", "WARNING")
    assert "Test warning message" in app.log_window.toHtml()
    assert "WARNING" in app.log_window.toHtml()
    
    # Test clear log
    app.handle_clear_all()
    assert app.log_window.toPlainText() == ""

@pytest.mark.gui
def test_query_handling(app, qtbot, mock_connection):
    """Test query handling functionality."""
    mock_conn, mock_cursor = mock_connection
    mock_cursor.description = [('type',), ('message',), ('details',)]
    mock_cursor.fetchall.return_value = [
        ('ERROR', 'Test error', '{"details": "test details"}')
    ]
    
    # Set up test connection
    app.conn = mock_conn
    app.table_input.setText("error_logs")
    app.query_btn.setEnabled(True)
    
    # Test successful query
    app.handle_query()
    assert app.results_table.rowCount() == 1
    assert app.results_table.columnCount() == 3
    assert app.results_table.horizontalHeaderItem(0).text() == "type"
    assert app.results_table.horizontalHeaderItem(1).text() == "message"
    assert app.results_table.horizontalHeaderItem(2).text() == "details"
    
    # Test query with empty table name
    app.table_input.clear()
    app.handle_query()
    assert "Please enter a table name" in app.log_window.toHtml()
    
    # Test query without connection
    app.conn = None
    app.handle_query()
    assert "Not connected to database" in app.log_window.toHtml()

@pytest.mark.gui
def test_connection_dialog(app, qtbot, mocker):
    """Test connection dialog functionality."""
    # Clear existing connections
    initial_connections_count = len(app.connections)
    app.connections = []
    
    # Mock the dialog
    mock_dialog = mocker.MagicMock()
    mock_dialog.exec.return_value = QDialog.Accepted
    mock_dialog.get_connection.return_value = {
        'name': 'Test Connection',
        'host': 'localhost',
        'port': '5432',
        'dbname': 'test_db',
        'user': 'test_user',
        'password': 'test_pass',
        'table': 'test_table'
    }
    mocker.patch('app.ConnectionDialog', return_value=mock_dialog)
    
    # Test adding connection
    app.handle_add_connection()
    assert len(app.connections) == 1
    assert app.connections[0]['name'] == 'Test Connection'
    
    # Test editing connection
    app.connection_combo.setCurrentIndex(1)
    app.handle_edit_connection()
    assert app.connections[0]['name'] == 'Test Connection'
    
    # Test deleting connection
    app.handle_delete_connection()
    assert len(app.connections) == 0
    assert app.connection_combo.currentIndex() == 0

@pytest.mark.gui
def test_database_connection(app, qtbot, mocker):
    """Test database connection functionality."""
    # Mock psycopg2.connect
    mock_conn = mocker.MagicMock()
    mocker.patch('psycopg2.connect', return_value=mock_conn)
    
    # Set up test connection data
    test_conn = {
        'name': 'Test Connection',
        'host': 'localhost',
        'port': '5432',
        'dbname': 'test_db',
        'user': 'test_user',
        'password': 'test_pass',
        'table': 'test_table'
    }
    app.connections.append(test_conn)
    app.update_connection_combo()
    app.connection_combo.setCurrentIndex(1)
    
    # Test successful connection
    app.handle_connect()
    assert app.conn == mock_conn
    assert app.connect_btn.isEnabled() == False
    assert app.disconnect_btn.isEnabled() == True
    assert app.query_btn.isEnabled() == True
    
    # Test disconnection
    app.handle_disconnect()
    assert app.conn is None
    assert app.connect_btn.isEnabled() == True
    assert app.disconnect_btn.isEnabled() == False
    assert app.query_btn.isEnabled() == False

@pytest.mark.gui
def test_error_handling(app, qtbot, mocker):
    """Test error handling functionality."""
    # Mock psycopg2.connect to raise an error
    mocker.patch('psycopg2.connect', side_effect=Error("Connection failed"))
    
    # Set up test connection data
    test_conn = {
        'name': 'Test Connection',
        'host': 'localhost',
        'port': '5432',
        'dbname': 'test_db',
        'user': 'test_user',
        'password': 'test_pass',
        'table': 'test_table'
    }
    app.connections.append(test_conn)
    app.update_connection_combo()
    app.connection_combo.setCurrentIndex(1)
    
    # Test connection error
    app.handle_connect()
    assert "Error connecting to database" in app.log_window.toHtml()
    assert app.conn is None
    assert app.connect_btn.isEnabled() == True
    assert app.disconnect_btn.isEnabled() == False
    assert app.query_btn.isEnabled() == False

@pytest.mark.gui
def test_menu_actions(app, qtbot, mocker):
    """Test menu actions functionality."""
    # Mock QMessageBox
    mock_msgbox = mocker.MagicMock()
    mock_msgbox.exec.return_value = QMessageBox.Yes
    mocker.patch('PySide6.QtWidgets.QMessageBox.question', return_value=mock_msgbox)
    
    # Test about dialog
    app.show_about()
    assert "About RVEB" in app.log_window.toHtml()
    
    # Test clear all action
    app.log_message("Test message", "INFO")
    app.handle_clear_all()
    assert app.log_window.toPlainText() == ""
    assert app.results_table.rowCount() == 0
    assert app.results_table.columnCount() == 0

@pytest.mark.gui
def test_connection_persistence(qtbot, mock_settings):
    """Test connection persistence functionality."""
    # Create a new app instance
    app = DatabaseApp()
    qtbot.addWidget(app)
    
    # Test saving connections
    test_conn = {
        'name': 'Test Connection',
        'host': 'localhost',
        'port': '5432',
        'dbname': 'test_db',
        'user': 'test_user',
        'password': 'test_pass',
        'table': 'test_table'
    }
    app.connections.append(test_conn)
    app.save_connections()
    
    # Verify that setValue was called with the correct arguments
    mock_settings.setValue.assert_called_once_with('connections', [test_conn])
    
    # Set up mock to return our test connection
    mock_settings.value.return_value = [test_conn]
    
    # Test loading connections
    app.connections = []
    app.load_connections()
    assert len(app.connections) == 1
    assert app.connections[0]['name'] == 'Test Connection' 