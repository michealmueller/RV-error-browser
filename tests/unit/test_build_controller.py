import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import QObject
from quantumops.controllers.build_controller import BuildController
from quantumops.models.build_manager import BuildManager
from quantumops.views.build_view import BuildView

@pytest.fixture
def mock_model():
    """Create a mock BuildManager."""
    model = Mock(spec=BuildManager)
    model.get_builds = Mock(return_value=[
        {"id": "test1", "version": "1.0", "status": "available"},
        {"id": "test2", "version": "1.1", "status": "downloaded"}
    ])
    return model

@pytest.fixture
def mock_view():
    """Create a mock BuildView."""
    view = Mock(spec=BuildView)
    view.platform = "android"
    return view

@pytest.fixture
def build_controller(mock_model, mock_view):
    """Create a BuildController instance with mocked dependencies."""
    return BuildController(mock_model, mock_view)

def test_init(build_controller, mock_model, mock_view):
    """Test controller initialization."""
    assert build_controller.model == mock_model
    assert build_controller.view == mock_view
    assert build_controller._progress_dialog is None

def test_handle_download_request_success(build_controller, mock_model, mock_view):
    """Test successful download request handling."""
    build_id = "test1"
    local_path = "/tmp/test1.apk"
    
    mock_model.download_build.return_value = local_path
    
    with patch.object(build_controller, '_show_progress_dialog') as mock_progress:
        mock_progress.return_value = Mock()
        build_controller._handle_download_request(build_id)
        
        mock_model.download_build.assert_called_once_with(
            build_id=build_id,
            platform=mock_view.platform,
            progress_callback=mock.ANY
        )
        mock_view.show_error.assert_not_called()

def test_handle_download_request_build_not_found(build_controller, mock_model, mock_view):
    """Test download request handling when build is not found."""
    build_id = "nonexistent"
    mock_model.get_builds.return_value = []
    
    build_controller._handle_download_request(build_id)
    
    mock_view.show_error.assert_called_once_with("Build not found")
    mock_model.download_build.assert_not_called()

def test_handle_upload_request_success(build_controller, mock_model, mock_view):
    """Test successful upload request handling."""
    build_id = "test1"
    local_path = "/tmp/test1.apk"
    blob_url = "https://storage.blob.core.windows.net/test1.apk"
    
    mock_model.upload_build.return_value = blob_url
    
    with patch.object(build_controller, '_show_progress_dialog') as mock_progress:
        mock_progress.return_value = Mock()
        build_controller._handle_upload_request(build_id, local_path)
        
        mock_model.upload_build.assert_called_once_with(
            build_id=build_id,
            local_path=local_path,
            platform=mock_view.platform,
            progress_callback=mock.ANY
        )
        mock_view.show_error.assert_not_called()

def test_handle_upload_request_file_not_found(build_controller, mock_model, mock_view):
    """Test upload request handling when file is not found."""
    build_id = "test1"
    local_path = "/nonexistent/test1.apk"
    
    with patch('os.path.exists', return_value=False):
        build_controller._handle_upload_request(build_id, local_path)
        
        mock_view.show_error.assert_called_once_with("Build file not found locally")
        mock_model.upload_build.assert_not_called()

def test_handle_install_request_success(build_controller, mock_model, mock_view):
    """Test successful install request handling."""
    build_id = "test1"
    local_path = "/tmp/test1.apk"
    
    mock_model.get_local_path.return_value = local_path
    
    with patch.object(build_controller, '_install_android_build') as mock_install:
        build_controller._handle_install_request(build_id)
        
        mock_install.assert_called_once_with(local_path)
        mock_view.show_error.assert_not_called()

def test_handle_install_request_build_not_found(build_controller, mock_model, mock_view):
    """Test install request handling when build is not found."""
    build_id = "nonexistent"
    mock_model.get_builds.return_value = []
    
    build_controller._handle_install_request(build_id)
    
    mock_view.show_error.assert_called_once_with("Build not found")
    mock_model.get_local_path.assert_not_called()

def test_cleanup(build_controller):
    """Test cleanup method."""
    mock_progress = Mock()
    build_controller._progress_dialog = mock_progress
    
    build_controller.cleanup()
    
    mock_progress.close.assert_called_once()
    assert build_controller._progress_dialog is None

def test_show_progress_dialog(build_controller):
    """Test showing progress dialog."""
    with patch('quantumops.controllers.build_controller.ProgressDialog') as mock_dialog:
        mock_dialog.return_value = Mock()
        
        result = build_controller._show_progress_dialog("Test Progress")
        
        mock_dialog.assert_called_once()
        assert result == mock_dialog.return_value

def test_handle_cancel(build_controller):
    """Test handling cancellation."""
    with patch('logging.Logger.info') as mock_log:
        build_controller._handle_cancel()
        mock_log.assert_called_once_with("Operation cancelled by user") 