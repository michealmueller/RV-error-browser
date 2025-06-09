import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from PySide6.QtWidgets import QProgressDialog, QMessageBox
from quantumops.controllers.build_controller import BuildController
from quantumops.views.build_view import BuildView
from quantumops.models.build_manager import BuildManager
from quantumops.services.azure_service import AzureServiceError

@pytest.fixture
def build_view(app):
    """Create a BuildView instance."""
    return BuildView(platform="android")

@pytest.fixture
def mock_model():
    """Create a mock BuildManager."""
    model = Mock(spec=BuildManager)
    model.initialize_azure = Mock()
    model.download_build = Mock()
    model.upload_build = Mock()
    model.fetch_builds = Mock()
    model.filter_builds = Mock()
    model.get_local_path = Mock(return_value=Path("/tmp/test-build"))
    return model

@pytest.fixture
def mock_azure_service():
    """Create a mock Azure service."""
    service = Mock()
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

def test_init(build_controller, build_view, mock_model):
    """Test BuildController initialization."""
    assert build_controller.view == build_view
    assert build_controller.model == mock_model
    assert build_controller._progress_dialog is None

def test_handle_download_request_success(build_controller, mock_model, tmp_path):
    """Test successful download request handling."""
    build_id = "test-build"
    platform = "android"
    local_path = tmp_path / f"{build_id}.apk"
    
    mock_model.download_build.return_value = str(local_path)
    
    with patch.object(build_controller, '_show_progress_dialog') as mock_show_progress:
        with patch.object(build_controller, '_hide_progress') as mock_hide_progress:
            build_controller._handle_download_request(build_id, platform)
            mock_model.download_build.assert_called_once_with(build_id, platform)
            mock_show_progress.assert_called_once()
            mock_hide_progress.assert_called_once()

def test_handle_download_request_build_not_found(build_controller, mock_model):
    """Test download request handling with non-existent build."""
    build_id = "test-build"
    platform = "android"
    
    mock_model.download_build.side_effect = ValueError("Build not found")
    
    with patch.object(build_controller, '_show_error') as mock_show_error:
        build_controller._handle_download_request(build_id, platform)
        mock_show_error.assert_called_once()

def test_handle_upload_request_success(build_controller, mock_model, tmp_path):
    """Test successful upload request handling."""
    build_id = "test-build"
    platform = "android"
    local_path = tmp_path / f"{build_id}.apk"
    local_path.touch()
    
    mock_model.upload_build.return_value = True
    
    with patch.object(build_controller, '_show_progress_dialog') as mock_show_progress:
        with patch.object(build_controller, '_hide_progress') as mock_hide_progress:
            build_controller._handle_upload_request(build_id, str(local_path), platform)
            mock_model.upload_build.assert_called_once_with(build_id, str(local_path), platform)
            mock_show_progress.assert_called_once()
            mock_hide_progress.assert_called_once()

def test_handle_upload_request_file_not_found(build_controller, mock_model):
    """Test upload request handling with non-existent file."""
    build_id = "test-build"
    platform = "android"
    local_path = "non-existent.apk"
    
    with patch.object(build_controller, '_show_error') as mock_show_error:
        build_controller._handle_upload_request(build_id, local_path, platform)
        mock_show_error.assert_called_once()

def test_handle_install_request_success(build_controller, mock_model, tmp_path):
    """Test successful install request handling."""
    build_id = "test-build"
    platform = "android"
    local_path = tmp_path / f"{build_id}.apk"
    local_path.touch()
    
    mock_model.get_local_path.return_value = str(local_path)
    
    with patch('subprocess.run') as mock_run:
        build_controller._handle_install_request(build_id, platform)
        mock_run.assert_called_once()

def test_handle_install_request_build_not_found(build_controller, mock_model):
    """Test install request handling with non-existent build."""
    build_id = "test-build"
    platform = "android"
    
    mock_model.get_local_path.side_effect = ValueError("Build not found")
    
    with patch.object(build_controller, '_show_error') as mock_show_error:
        build_controller._handle_install_request(build_id, platform)
        mock_show_error.assert_called_once()
        mock_model.get_local_path.assert_not_called()

def test_cleanup(build_controller):
    """Test cleanup."""
    build_controller._progress_dialog = Mock(spec=QProgressDialog)
    build_controller.cleanup()
    assert build_controller._progress_dialog is None

def test_show_progress_dialog(build_controller):
    """Test progress dialog display."""
    build_controller._show_progress_dialog("Test", "Test message")
    assert isinstance(build_controller._progress_dialog, QProgressDialog)
    assert build_controller._progress_dialog.labelText() == "Test message"

def test_handle_cancel(build_controller):
    """Test cancel handling."""
    build_controller._progress_dialog = Mock(spec=QProgressDialog)
    build_controller._handle_cancel()
    assert build_controller._progress_dialog is None 