"""
Unit tests for BuildManager.
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from quantumops.models.build_manager import BuildManager
from quantumops.services.azure_service import AzureService, AzureServiceError

@pytest.fixture
def mock_azure_service():
    """Create a mock Azure service."""
    mock = Mock(spec=AzureService)
    mock.initialize = Mock()
    mock.download_file = Mock()
    mock.upload_file = Mock()
    mock.list_files = Mock()
    mock.get_file_metadata = Mock()
    mock.update_file_metadata = Mock()
    mock.cleanup = Mock()
    return mock

@pytest.fixture
def build_manager(mock_azure_service):
    """Create a BuildManager instance with mocked Azure service."""
    manager = BuildManager()
    manager.azure_service = mock_azure_service
    return manager

def test_initialize_azure_success(build_manager, mock_azure_service):
    """Test successful Azure initialization."""
    build_manager.initialize_azure("test-container")
    mock_azure_service.initialize.assert_called_once_with("test-container")

def test_initialize_azure_error(build_manager, mock_azure_service):
    """Test Azure initialization error."""
    mock_azure_service.initialize.side_effect = AzureServiceError("Azure error")
    with pytest.raises(AzureServiceError) as exc_info:
        build_manager.initialize_azure("test-container")
    assert "Azure error" in str(exc_info.value)

def test_download_build_success(build_manager, mock_azure_service, tmp_path):
    """Test successful build download."""
    build_id = "test-build"
    platform = "android"
    local_path = tmp_path / f"{build_id}.apk"
    
    mock_azure_service.get_file_metadata.return_value = {
        "metadata": {"version": "1.0.0"}
    }
    mock_azure_service.download_file.return_value = str(local_path)
    
    result = build_manager.download_build(build_id, platform)
    assert result == str(local_path)
    mock_azure_service.download_file.assert_called_once()

def test_download_build_not_found(build_manager, mock_azure_service):
    """Test download of non-existent build."""
    build_id = "test-build"
    platform = "android"
    mock_azure_service.get_file_metadata.side_effect = AzureServiceError("File not found")
    with pytest.raises(ValueError) as exc_info:
        build_manager.download_build(build_id, platform)
    assert "Build file not found" in str(exc_info.value)

def test_download_build_azure_error(build_manager, mock_azure_service):
    """Test Azure error during build download."""
    build_id = "test-build"
    platform = "android"
    
    mock_azure_service.download_file.side_effect = AzureServiceError("Azure error")
    
    with pytest.raises(AzureServiceError) as exc_info:
        build_manager.download_build(build_id, platform)
    assert "Azure error" in str(exc_info.value)

def test_upload_build_success(build_manager, mock_azure_service, tmp_path):
    """Test successful build upload."""
    build_id = "test-build"
    platform = "android"
    local_path = tmp_path / f"{build_id}.apk"
    local_path.touch()
    
    mock_azure_service.upload_file.return_value = True
    
    result = build_manager.upload_build(build_id, str(local_path), platform)
    assert result is True
    mock_azure_service.upload_file.assert_called_once()

def test_upload_build_not_found(build_manager, mock_azure_service):
    """Test upload of non-existent build file."""
    build_id = "test-build"
    platform = "android"
    local_path = "non-existent.apk"
    with pytest.raises(ValueError) as exc_info:
        build_manager.upload_build(build_id, local_path, platform)
    assert "Build file not found" in str(exc_info.value)

def test_upload_build_file_not_found(build_manager, mock_azure_service):
    """Test upload with non-existent file."""
    build_id = "test-build"
    platform = "android"
    local_path = "non-existent.apk"
    
    with pytest.raises(ValueError) as exc_info:
        build_manager.upload_build(build_id, local_path, platform)
    assert "Build file not found" in str(exc_info.value)

def test_upload_build_azure_error(build_manager, mock_azure_service, tmp_path):
    """Test Azure error during build upload."""
    build_id = "test-build"
    platform = "android"
    local_path = tmp_path / f"{build_id}.apk"
    local_path.touch()
    
    mock_azure_service.upload_file.side_effect = AzureServiceError("Azure error")
    
    with pytest.raises(AzureServiceError) as exc_info:
        build_manager.upload_build(build_id, str(local_path), platform)
    assert "Azure error" in str(exc_info.value)

def test_fetch_builds_success(build_manager, mock_azure_service):
    """Test successful build fetch."""
    platform = "android"
    mock_files = [
        {
            "name": "build1.apk",
            "metadata": {"version": "1.0.0"}
        },
        {
            "name": "build2.apk",
            "metadata": {"version": "2.0.0"}
        }
    ]
    mock_azure_service.list_files.return_value = mock_files
    
    result = build_manager.fetch_builds(platform)
    assert len(result) == 2
    assert result[0]["version"] == "1.0.0"
    assert result[1]["version"] == "2.0.0"

def test_fetch_builds_azure_error(build_manager, mock_azure_service):
    """Test Azure error during build fetch."""
    platform = "android"
    mock_azure_service.list_files.side_effect = AzureServiceError("Azure error")
    
    with pytest.raises(AzureServiceError) as exc_info:
        build_manager.fetch_builds(platform)
    assert "Azure error fetching builds" in str(exc_info.value)

def test_filter_builds_success(build_manager):
    """Test successful build filtering."""
    builds = [
        {"id": "build1", "version": "1.0"},
        {"id": "build2", "version": "2.0"}
    ]
    filter_text = "1.0"
    
    result = build_manager.filter_builds(builds, filter_text)
    assert len(result) == 1
    assert result[0]["id"] == "build1"

def test_filter_builds_empty(build_manager):
    """Test filtering with empty results."""
    builds = [
        {"id": "build1", "version": "1.0"},
        {"id": "build2", "version": "2.0"}
    ]
    filter_text = "3.0"
    
    result = build_manager.filter_builds(builds, filter_text)
    assert len(result) == 0

def test_filter_builds_error(build_manager):
    """Test build filtering error."""
    builds = None
    filter_text = "1.0"
    
    with pytest.raises(ValueError) as exc_info:
        build_manager.filter_builds(builds, filter_text)
    assert "Invalid builds list" in str(exc_info.value) 