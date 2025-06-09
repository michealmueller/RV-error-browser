import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import Qt
from quantumops.views.build_view import BuildView

@pytest.fixture
def build_view(qapp):
    """Create a BuildView instance."""
    return BuildView(platform="android")

def test_init(build_view):
    """Test view initialization."""
    assert build_view.platform == "android"
    assert build_view.search_input is not None
    assert build_view.version_filter is not None
    assert build_view.status_filter is not None
    assert build_view.builds_table is not None
    assert build_view.status_bar is not None

def test_handle_search(build_view):
    """Test search handling."""
    with patch.object(build_view, 'filter_changed') as mock_filter:
        build_view.search_input.setText("test")
        mock_filter.emit.assert_called_once_with({
            "search": "test",
            "version": "",
            "status": ""
        })

def test_handle_filter_change(build_view):
    """Test filter change handling."""
    with patch.object(build_view, 'filter_changed') as mock_filter:
        build_view.version_filter.setCurrentIndex(1)  # Select first version
        mock_filter.emit.assert_called_once_with({
            "search": "",
            "version": build_view.version_filter.currentData(),
            "status": ""
        })

def test_handle_selection(build_view):
    """Test build selection handling."""
    # Add a test build to the table
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, QTableWidgetItem("test1"))
    
    with patch.object(build_view, 'build_selected') as mock_selected, \
         patch.object(build_view, 'upload_requested') as mock_upload:
        build_view.builds_table.selectRow(0)
        
        mock_selected.emit.assert_called_once_with("test1")
        mock_upload.emit.assert_called_once_with("test1", "/tmp/builds/test1")

def test_get_local_path(build_view):
    """Test getting local path for a build."""
    path = build_view.get_local_path("test1")
    assert path == "/tmp/builds/test1"

def test_show_error(build_view):
    """Test showing error message."""
    with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical:
        build_view._show_error("Test Error", "Test message")
        mock_critical.assert_called_once()

def test_update_builds_empty(build_view):
    """Test updating builds table with empty list."""
    build_view.update_builds([])
    assert build_view.builds_table.rowCount() == 0
    assert build_view.status_bar.text() == "No builds found"

def test_update_builds_with_data(build_view):
    """Test updating builds table with data."""
    builds = [
        {
            "id": "test1",
            "version": "1.0",
            "status": "available",
            "size": 1000,
            "date": "2024-01-01"
        },
        {
            "id": "test2",
            "version": "1.1",
            "status": "downloaded",
            "size": 2000,
            "date": "2024-01-02"
        }
    ]
    
    build_view.update_builds(builds)
    
    assert build_view.builds_table.rowCount() == 2
    assert build_view.status_bar.text() == "Showing 2 builds"
    
    # Check first row
    assert build_view.builds_table.item(0, 0).text() == "test1"
    assert build_view.builds_table.item(0, 1).text() == "1.0"
    assert build_view.builds_table.item(0, 2).text() == "available"
    assert build_view.builds_table.item(0, 3).text() == "1000"
    assert build_view.builds_table.item(0, 4).text() == "2024-01-01"

def test_update_build_status(build_view):
    """Test updating build status."""
    # Add a test build to the table
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, QTableWidgetItem("test1"))
    build_view.builds_table.setItem(0, 2, QTableWidgetItem("old_status"))
    
    build_view.update_build_status("test1", "new_status")
    assert build_view.builds_table.item(0, 2).text() == "new_status"

def test_update_upload_status(build_view):
    """Test updating upload status."""
    # Add a test build to the table
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, QTableWidgetItem("test1"))
    build_view.builds_table.setItem(0, 2, QTableWidgetItem("downloaded"))
    
    build_view.update_upload_status("test1", "uploaded to Azure")
    assert build_view.builds_table.item(0, 2).text() == "downloaded - uploaded to Azure"

def test_update_upload_retry(build_view):
    """Test updating upload retry status."""
    # Add a test build to the table
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, QTableWidgetItem("test1"))
    build_view.builds_table.setItem(0, 2, QTableWidgetItem("downloaded"))
    
    build_view.update_upload_retry("test1", 2)
    assert build_view.builds_table.item(0, 2).text() == "downloaded (Retry 2)"

def test_cleanup(build_view):
    """Test cleanup method."""
    # Add some data to the view
    build_view.search_input.setText("test")
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, QTableWidgetItem("test1"))
    build_view.status_bar.setText("Test status")
    
    build_view.cleanup()
    
    assert build_view.search_input.text() == ""
    assert build_view.builds_table.rowCount() == 0
    assert build_view.status_bar.text() == ""
    assert build_view.version_filter.currentIndex() == 0
    assert build_view.status_filter.currentIndex() == 0 