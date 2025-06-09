import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from quantumops.controllers.build_controller import BuildController
from quantumops.views.build_view import BuildView
from quantumops.services.azure_service import AzureService
from quantumops.models.build_manager import BuildManager

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture
def mock_azure_service():
    """Create a mock AzureService."""
    service = MagicMock(spec=AzureService)
    service.initialize.return_value = True
    return service

@pytest.fixture
def build_manager(temp_dir, mock_azure_service):
    """Create a BuildManager instance with mocked AzureService."""
    manager = BuildManager()
    manager._azure_service = mock_azure_service
    manager._download_dir = temp_dir
    return manager

@pytest.fixture
def build_view(qapp):
    """Create a BuildView instance."""
    return BuildView(platform="android")

@pytest.fixture
def build_controller(build_manager, build_view):
    """Create a BuildController instance."""
    return BuildController(build_manager, build_view)

def test_build_download_flow(build_controller, build_view, mock_azure_service, temp_dir):
    """Test the complete build download flow."""
    # Setup test data
    build_id = "test_build_1"
    test_file = os.path.join(temp_dir, "test_build_1.apk")
    with open(test_file, "w") as f:
        f.write("test content")
    
    # Mock Azure service responses
    mock_azure_service.download_file.return_value = None
    mock_azure_service.get_file_metadata.return_value = {
        "size": 1000,
        "last_modified": "2024-01-01",
        "metadata": {"version": "1.0"}
    }
    
    # Trigger download
    build_controller._handle_download_request(build_id)
    
    # Verify Azure service calls
    mock_azure_service.download_file.assert_called_once()
    mock_azure_service.get_file_metadata.assert_called_once()
    
    # Verify view updates
    assert build_view.builds_table.rowCount() > 0
    status_item = build_view.builds_table.item(0, 2)
    assert status_item is not None
    assert "downloaded" in status_item.text().lower()

def test_build_upload_flow(build_controller, build_view, mock_azure_service, temp_dir):
    """Test the complete build upload flow."""
    # Setup test data
    build_id = "test_build_1"
    test_file = os.path.join(temp_dir, "test_build_1.apk")
    with open(test_file, "w") as f:
        f.write("test content")
    
    # Mock Azure service responses
    mock_azure_service.upload_file.return_value = None
    mock_azure_service.get_file_metadata.return_value = {
        "size": 1000,
        "last_modified": "2024-01-01",
        "metadata": {"version": "1.0"}
    }
    
    # Add build to view
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, MagicMock(text=build_id))
    build_view.builds_table.setItem(0, 2, MagicMock(text="downloaded"))
    
    # Trigger upload
    build_controller._handle_upload_request(build_id)
    
    # Verify Azure service calls
    mock_azure_service.upload_file.assert_called_once()
    
    # Verify view updates
    status_item = build_view.builds_table.item(0, 2)
    assert status_item is not None
    assert "uploaded" in status_item.text().lower()

def test_build_install_flow(build_controller, build_view, temp_dir):
    """Test the complete build installation flow."""
    # Setup test data
    build_id = "test_build_1"
    test_file = os.path.join(temp_dir, "test_build_1.apk")
    with open(test_file, "w") as f:
        f.write("test content")
    
    # Add build to view
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, MagicMock(text=build_id))
    build_view.builds_table.setItem(0, 2, MagicMock(text="downloaded"))
    
    # Mock adb commands
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        
        # Trigger installation
        build_controller._handle_install_request(build_id)
        
        # Verify adb calls
        mock_run.assert_called()
        
        # Verify view updates
        status_item = build_view.builds_table.item(0, 2)
        assert status_item is not None
        assert "installed" in status_item.text().lower()

def test_error_handling_flow(build_controller, build_view, mock_azure_service):
    """Test error handling flow."""
    # Setup test data
    build_id = "test_build_1"
    
    # Mock Azure service error
    mock_azure_service.download_file.side_effect = Exception("Test error")
    
    # Add build to view
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, MagicMock(text=build_id))
    build_view.builds_table.setItem(0, 2, MagicMock(text="available"))
    
    # Mock QMessageBox
    with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical:
        # Trigger download
        build_controller._handle_download_request(build_id)
        
        # Verify error message was shown
        mock_critical.assert_called_once()
        
        # Verify view updates
        status_item = build_view.builds_table.item(0, 2)
        assert status_item is not None
        assert "error" in status_item.text().lower()

def test_filter_and_search_flow(build_controller, build_view):
    """Test filtering and searching flow."""
    # Setup test data
    builds = [
        {"id": "test1", "version": "1.0", "status": "available"},
        {"id": "test2", "version": "1.1", "status": "downloaded"},
        {"id": "test3", "version": "1.0", "status": "installed"}
    ]
    
    # Update view with builds
    build_view.update_builds(builds)
    
    # Test search
    build_view.search_input.setText("test1")
    assert build_view.builds_table.rowCount() == 1
    assert build_view.builds_table.item(0, 0).text() == "test1"
    
    # Test version filter
    build_view.version_filter.setCurrentText("1.0")
    assert build_view.builds_table.rowCount() == 2
    
    # Test status filter
    build_view.status_filter.setCurrentText("downloaded")
    assert build_view.builds_table.rowCount() == 1
    assert build_view.builds_table.item(0, 0).text() == "test2"

def test_cleanup_flow(build_controller, build_view, mock_azure_service):
    """Test cleanup flow."""
    # Setup test data
    build_id = "test_build_1"
    build_view.builds_table.setRowCount(1)
    build_view.builds_table.setItem(0, 0, MagicMock(text=build_id))
    build_view.search_input.setText("test")
    build_view.status_bar.setText("Test status")
    
    # Trigger cleanup
    build_controller.cleanup()
    
    # Verify view cleanup
    assert build_view.builds_table.rowCount() == 0
    assert build_view.search_input.text() == ""
    assert build_view.status_bar.text() == ""
    
    # Verify Azure service cleanup
    mock_azure_service.cleanup.assert_called_once() 