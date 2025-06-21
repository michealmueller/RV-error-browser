import os
import sys

import psycopg2
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from tests.db_config import DB_CONFIG

TEST_CONN = {
    "name": "TestConn",
    "host": DB_CONFIG["host"],
    "port": DB_CONFIG["port"],
    "dbname": DB_CONFIG["database"],
    "user": DB_CONFIG["username"],
    "password": DB_CONFIG["password"],
    "table": DB_CONFIG["default_table"],
}


@pytest.fixture(scope="function", autouse=True)
def setup_test_table():
    """Ensure the test table exists with the correct schema before each test."""
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["username"],
        password=DB_CONFIG["password"],
    )
    cur = conn.cursor()
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {DB_CONFIG['default_table']} (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50),
            message TEXT,
            details TEXT
        )
    """
    )
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
def close_app_conn(app):
    yield
    if hasattr(app, "conn") and app.conn:
        app.conn.close()
        app.conn = None


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for testing."""
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
        # Set environment variable to indicate we're running in a test environment
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def app(qapp):
    """Create a DatabaseApp instance for testing."""
    from main_window import DatabaseApp

    app = DatabaseApp()
    yield app
    app.close()


@pytest.mark.timeout(10)
def test_application_startup(app):
    """Test that the application starts up correctly and is visible."""
    app.show()  # Ensure the window is shown
    assert app.isVisible()
    assert app.windowTitle() == "QuantumOps"


@pytest.mark.timeout(30)
def test_database_connection(app, qtbot):
    """Test connecting to the database via the connection combo."""
    # Ensure password is present and selected
    app.connections.append(TEST_CONN)
    app.update_connection_combo()
    app.connection_combo.setCurrentIndex(1)  # Select the first real connection
    # Simulate connect button click
    qtbot.mouseClick(app.connect_btn, Qt.LeftButton)
    assert app.conn is not None


@pytest.mark.timeout(30)
def test_query_execution(app, qtbot):
    """Test executing a query after connecting to the database."""
    # Insert a test row into the table before querying
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["username"],
        password=DB_CONFIG["password"],
    )
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO {DB_CONFIG['default_table']}(type, message, details) VALUES ('test', 'test message', 'test details')"
    )
    conn.commit()
    cur.close()
    conn.close()
    test_database_connection(app, qtbot)
    app.query_btn.setEnabled(True)
    qtbot.mouseClick(app.query_btn, Qt.LeftButton)
    # Check that results table is populated
    assert app.results_table.rowCount() > 0
    assert app.results_table.columnCount() > 0


@pytest.mark.timeout(20)
def test_connection_management(app, qtbot):
    """Test managing database connections via the Add button."""
    qtbot.mouseClick(app.add_conn_btn, Qt.LeftButton)
    # The dialog will appear; further dialog interaction would require more advanced qtbot usage or mocking.


@pytest.mark.timeout(15)
def test_error_handling(app, qtbot):
    """Test error handling."""
    # Try to connect with invalid credentials
    app.host_label.setText("invalid_host")
    qtbot.mouseClick(app.connect_btn, Qt.LeftButton)
    assert "Error" in app.log_window.toPlainText()

    # Try to execute query without connection
    qtbot.mouseClick(app.query_btn, Qt.LeftButton)
    assert "Error" in app.log_window.toPlainText()
