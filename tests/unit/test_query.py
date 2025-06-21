import pytest
from PySide6.QtCore import Qt

from main_window import DatabaseApp


@pytest.fixture
def app(qtbot):
    """Create the application window."""
    window = DatabaseApp()
    qtbot.addWidget(window)
    return window


def test_query_results_formatting(app):
    """Test that query results are formatted correctly."""
    # Set test data
    headers = ["id", "timestamp", "level", "message"]
    data = [
        (1, "2024-01-01", "INFO", "Test message 1"),
        (2, "2024-01-02", "ERROR", "Test message 2"),
    ]

    # Set query results
    app.set_query_results(headers, data)

    # Check table structure
    assert app.results_table.rowCount() == 2
    assert app.results_table.columnCount() == 4

    # Check headers
    for i, header in enumerate(headers):
        assert app.results_table.horizontalHeaderItem(i).text() == header

    # Check data
    for row, (id_val, timestamp, level, message) in enumerate(data):
        assert app.results_table.item(row, 0).text() == str(id_val)
        assert app.results_table.item(row, 1).text() == timestamp
        assert app.results_table.item(row, 2).text() == level
        assert app.results_table.item(row, 3).text() == message


def test_query_results_clear(app):
    """Test clearing query results."""
    # Set test data
    headers = ["id", "message"]
    data = [(1, "Test message")]
    app.set_query_results(headers, data)

    # Clear results
    app.clear_results()

    # Check that table is empty
    assert app.results_table.rowCount() == 0
    assert app.results_table.columnCount() == 0


def test_query_results_sorting(app):
    """Test that query results can be sorted."""
    # Set test data
    headers = ["id", "message"]
    data = [(2, "Message 2"), (1, "Message 1"), (3, "Message 3")]
    app.set_query_results(headers, data)

    # Sort by ID
    app.results_table.sortItems(0, Qt.AscendingOrder)

    # Check sorted order
    assert app.results_table.item(0, 0).text() == "1"
    assert app.results_table.item(1, 0).text() == "2"
    assert app.results_table.item(2, 0).text() == "3"


def test_query_results_selection(app):
    """Test selecting rows in query results."""
    # Set test data
    headers = ["id", "message"]
    data = [(1, "Test message")]
    app.set_query_results(headers, data)

    # Select first row
    app.results_table.selectRow(0)

    # Check selection
    assert app.results_table.selectedItems()
    assert app.results_table.selectedItems()[0].text() == "1"


def test_query_results_resize(app):
    """Test that query results table resizes correctly."""
    # Set test data
    headers = ["id", "message"]
    data = [(1, "Test message")]
    app.set_query_results(headers, data)

    # Resize window
    app.resize(800, 600)

    # Check that table fills available space
    assert app.results_table.width() > 0
    assert app.results_table.height() > 0
