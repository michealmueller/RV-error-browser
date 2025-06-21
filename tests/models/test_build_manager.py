"""
Unit tests for BuildManager.
"""
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from models.build_manager import BuildManager
from services.azure_service import AzureServiceError


@pytest.fixture
def mock_azure_service():
    """Create a mock AzureService."""
    with patch("quantumops.models.build_manager.AzureService") as mock:
        yield mock.return_value


@pytest.fixture
def build_manager(mock_azure_service):
    """Create a BuildManager instance for testing with a mocked AzureService."""
    manager = BuildManager()
    manager._azure_service = mock_azure_service
    return manager


def test_initialize_azure_success(build_manager, mock_azure_service):
    """Test successful Azure initialization."""
    # Arrange
    container_name = "test-container"

    # Act
    build_manager.initialize_azure(container_name)

    # Assert
    mock_azure_service.initialize.assert_called_once_with(container_name)


def test_initialize_azure_error(build_manager, mock_azure_service):
    """Test Azure initialization error."""
    # Arrange
    container_name = "test-container"
    mock_azure_service.initialize.side_effect = AzureServiceError("Azure error")

    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        build_manager.initialize_azure(container_name)
    assert str(exc_info.value) == "Azure error"


def test_download_build_success(build_manager, mock_azure_service):
    """Test successful build download."""
    # Arrange
    build_id = "test-build"
    platform = "android"
    # The expected local path is constructed by BuildManager
    expected_local_path = str(
        Path.home() / ".quantumops" / "downloads" / platform / f"{build_id}.apk"
    )

    build_manager._builds[platform] = [{"id": build_id, "status": "available"}]

    mock_azure_service.download_file.return_value = expected_local_path

    # Act
    result = build_manager.download_build(build_id=build_id, platform=platform)

    # Assert
    assert result == expected_local_path
    assert build_manager._builds[platform][0]["status"] == "downloaded"
    assert build_manager._builds[platform][0]["local_path"] == expected_local_path


def test_download_build_not_found(build_manager):
    """Test download of non-existent build."""
    # Arrange
    build_id = "nonexistent-build"
    platform = "android"

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        build_manager.download_build(build_id, platform)
    assert f"Build {build_id} not found" in str(exc_info.value)


def test_download_build_azure_error(build_manager, mock_azure_service):
    """Test download with Azure error."""
    # Arrange
    build_id = "test-build"
    platform = "android"

    build_manager._builds[platform] = [{"id": build_id, "status": "available"}]

    mock_azure_service.download_file.side_effect = AzureServiceError("Azure error")

    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        build_manager.download_build(build_id, platform)
    assert str(exc_info.value) == "Azure error"


def test_upload_build_success(build_manager, mock_azure_service):
    """Test successful build upload."""
    # Arrange
    build_id = "test-build"
    platform = "android"
    blob_url = "https://storage.blob.core.windows.net/test-container/test-build.apk"

    # Create a temporary file to upload
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        local_path = tmp_file.name
        tmp_file.write(b"dummy content")

    build_manager._builds[platform] = [{"id": build_id, "status": "downloaded"}]

    mock_azure_service.upload_file.return_value = blob_url

    # Act
    result = build_manager.upload_build(
        build_id=build_id, local_path=local_path, platform=platform
    )

    # Assert
    assert result == blob_url
    assert build_manager._builds[platform][0]["status"] == "uploaded"
    assert build_manager._builds[platform][0]["blob_url"] == blob_url

    # Cleanup
    Path(local_path).unlink(missing_ok=True)


def test_upload_build_not_found(build_manager):
    """Test upload of non-existent build."""
    # Arrange
    build_id = "nonexistent-build"
    platform = "android"
    local_path = "/path/to/build.apk"

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        build_manager.upload_build(build_id, local_path, platform)
    assert f"Build {build_id} not found" in str(exc_info.value)


def test_upload_build_file_not_found(build_manager, mock_azure_service):
    """Test upload with non-existent file."""
    # Arrange
    build_id = "test-build"
    platform = "android"
    local_path = "/nonexistent/path/build.apk"

    build_manager._builds[platform] = [{"id": build_id, "status": "downloaded"}]

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        build_manager.upload_build(build_id, local_path, platform)
    assert f"Build file not found: {local_path}" in str(exc_info.value)


def test_upload_build_azure_error(build_manager, mock_azure_service):
    """Test upload with Azure error."""
    # Arrange
    build_id = "test-build"
    platform = "android"
    # Create a temporary file to upload
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        local_path = tmp_file.name
        tmp_file.write(b"dummy content")

    build_manager._builds[platform] = [{"id": build_id, "status": "downloaded"}]

    mock_azure_service.upload_file.side_effect = AzureServiceError("Azure error")

    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        build_manager.upload_build(build_id, local_path, platform)
    assert str(exc_info.value) == "Azure error"

    # Cleanup
    Path(local_path).unlink(missing_ok=True)


def test_fetch_builds_success(build_manager, mock_azure_service):
    """Test successful build fetching."""
    # Arrange
    platform = "android"
    files = ["build1.apk", "build2.apk"]
    metadata = {
        "build1.apk": {
            "size": 100,
            "last_modified": datetime.now(),
            "metadata": {"version": "1.0"},
        },
        "build2.apk": {
            "size": 200,
            "last_modified": datetime.now(),
            "metadata": {"version": "2.0"},
        },
    }

    mock_azure_service.list_files.return_value = files
    mock_azure_service.get_file_metadata.side_effect = lambda name: metadata[name]

    # Act
    result = build_manager.fetch_builds(platform)

    # Assert
    assert len(result) == 2
    assert result[0]["id"] == "build1.apk"
    assert result[0]["version"] == "1.0"
    assert result[1]["id"] == "build2.apk"
    assert result[1]["version"] == "2.0"


def test_fetch_builds_azure_error(build_manager, mock_azure_service):
    """Test fetch builds with Azure error."""
    # Arrange
    platform = "android"
    mock_azure_service.list_files.side_effect = AzureServiceError("Azure error")

    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        build_manager.fetch_builds(platform)
    assert str(exc_info.value) == "Azure error"


def test_filter_builds_success(build_manager):
    """Test successful build filtering."""
    # Arrange
    platform = "android"
    builds = [
        {"id": "build1", "version": "1.0", "status": "available"},
        {"id": "build2", "version": "2.0", "status": "downloaded"},
        {"id": "build3", "version": "1.0", "status": "uploaded"},
    ]

    build_manager._builds[platform] = builds

    # Test version filter
    version_filter = {"version": "1.0"}
    version_result = build_manager.filter_builds(platform, version_filter)
    assert len(version_result) == 2
    assert all(b["version"] == "1.0" for b in version_result)

    # Test status filter
    status_filter = {"status": "downloaded"}
    status_result = build_manager.filter_builds(platform, status_filter)
    assert len(status_result) == 1
    assert status_result[0]["status"] == "downloaded"

    # Test search filter
    search_filter = {"search": "build1"}
    search_result = build_manager.filter_builds(platform, search_filter)
    assert len(search_result) == 1
    assert search_result[0]["id"] == "build1"


def test_filter_builds_empty(build_manager):
    """Test filtering with no builds."""
    # Arrange
    platform = "android"
    build_manager._builds[platform] = []

    # Act
    result = build_manager.filter_builds(platform, {"version": "1.0"})

    # Assert
    assert result == []


def test_filter_builds_error(build_manager):
    """Test filtering with error."""
    # Arrange
    platform = "android"
    build_manager._builds[platform] = None

    # Act
    result = build_manager.filter_builds(platform, {"version": "1.0"})

    # Assert
    assert result == []
