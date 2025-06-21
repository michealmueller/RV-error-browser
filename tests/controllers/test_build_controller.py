"""
Unit tests for BuildController.
"""
from unittest.mock import Mock, patch

import pytest

from controllers.build_controller import BuildController
from models.build_manager import BuildManager
from services.azure_service import AzureServiceError


@pytest.fixture
def build_manager():
    """Create a BuildManager instance for testing."""
    return Mock(spec=BuildManager)


@pytest.fixture
def build_controller(build_manager):
    """Create a BuildController instance for testing."""
    controller = BuildController(build_manager)
    return controller


@pytest.fixture
def mock_progress_dialog():
    """Create a mock ProgressDialog."""
    with patch("quantumops.controllers.build_controller.ProgressDialog") as mock:
        yield mock


@pytest.fixture
def mock_message_box():
    """Create a mock QMessageBox."""
    with patch("quantumops.controllers.build_controller.QMessageBox") as mock:
        yield mock


def test_initialize_azure_success(build_controller, build_manager):
    """Test successful Azure initialization."""
    # Arrange
    container_name = "test-container"

    # Act
    build_controller.initialize_azure(container_name)

    # Assert
    build_manager.initialize_azure.assert_called_once_with(container_name)


def test_initialize_azure_error(build_controller, build_manager, mock_message_box):
    """Test Azure initialization error."""
    # Arrange
    container_name = "test-container"
    error_msg = "Azure error"
    build_manager.initialize_azure.side_effect = AzureServiceError(error_msg)

    # Act
    build_controller.initialize_azure(container_name)

    # Assert
    mock_message_box.critical.assert_called_once()
    assert error_msg in str(mock_message_box.critical.call_args[0][2])


def test_fetch_builds_success(build_controller, build_manager, mock_progress_dialog):
    """Test successful build fetching."""
    # Arrange
    platform = "android"
    builds = [{"id": "build1"}, {"id": "build2"}]
    build_manager.fetch_builds.return_value = builds

    # Act
    build_controller.fetch_builds(platform)

    # Assert
    build_manager.fetch_builds.assert_called_once()
    mock_progress_dialog.assert_called_once()
    mock_progress_dialog.return_value.close.assert_called_once()


def test_fetch_builds_error(
    build_controller, build_manager, mock_progress_dialog, mock_message_box
):
    """Test fetch builds with error."""
    # Arrange
    platform = "android"
    error_msg = "Azure error"
    build_manager.fetch_builds.side_effect = AzureServiceError(error_msg)

    # Act
    build_controller.fetch_builds(platform)

    # Assert
    mock_message_box.critical.assert_called_once()
    assert error_msg in str(mock_message_box.critical.call_args[0][2])
    mock_progress_dialog.return_value.close.assert_called_once()


def test_download_build_success(
    build_controller, build_manager, mock_progress_dialog, mock_message_box
):
    """Test successful build download."""
    # Arrange
    build_id = "test-build"
    platform = "android"
    local_path = "/path/to/download.apk"
    build_manager.download_build.return_value = local_path

    # Act
    build_controller.download_build(build_id, platform)

    # Assert
    build_manager.download_build.assert_called_once()
    mock_progress_dialog.assert_called_once()
    mock_progress_dialog.return_value.close.assert_called_once()
    mock_message_box.information.assert_called_once()
    assert local_path in str(mock_message_box.information.call_args[0][2])


def test_download_build_error(
    build_controller, build_manager, mock_progress_dialog, mock_message_box
):
    """Test download build with error."""
    # Arrange
    build_id = "test-build"
    platform = "android"
    error_msg = "Azure error"
    build_manager.download_build.side_effect = AzureServiceError(error_msg)

    # Act
    build_controller.download_build(build_id, platform)

    # Assert
    mock_message_box.critical.assert_called_once()
    assert error_msg in str(mock_message_box.critical.call_args[0][2])
    mock_progress_dialog.return_value.close.assert_called_once()


def test_upload_build_success(
    build_controller, build_manager, mock_progress_dialog, mock_message_box
):
    """Test successful build upload."""
    # Arrange
    build_id = "test-build"
    platform = "android"
    local_path = "/path/to/build.apk"
    blob_url = "https://storage.blob.core.windows.net/test-container/test-build.apk"
    build_manager.upload_build.return_value = blob_url

    # Act
    build_controller.upload_build(build_id, local_path, platform)

    # Assert
    build_manager.upload_build.assert_called_once()
    mock_progress_dialog.assert_called_once()
    mock_progress_dialog.return_value.close.assert_called_once()
    mock_message_box.information.assert_called_once()
    assert blob_url in str(mock_message_box.information.call_args[0][2])


def test_upload_build_error(
    build_controller, build_manager, mock_progress_dialog, mock_message_box
):
    """Test upload build with error."""
    # Arrange
    build_id = "test-build"
    platform = "android"
    local_path = "/path/to/build.apk"
    error_msg = "Azure error"
    build_manager.upload_build.side_effect = AzureServiceError(error_msg)

    # Act
    build_controller.upload_build(build_id, local_path, platform)

    # Assert
    mock_message_box.critical.assert_called_once()
    assert error_msg in str(mock_message_box.critical.call_args[0][2])
    mock_progress_dialog.return_value.close.assert_called_once()


def test_filter_builds_success(build_controller, build_manager):
    """Test successful build filtering."""
    # Arrange
    platform = "android"
    filters = {"version": "1.0"}
    filtered_builds = [{"id": "build1", "version": "1.0"}]
    build_manager.filter_builds.return_value = filtered_builds

    # Act
    result = build_controller.filter_builds(platform, filters)

    # Assert
    build_manager.filter_builds.assert_called_once_with(platform, filters)
    assert result == filtered_builds


def test_filter_builds_error(build_controller, build_manager, mock_message_box):
    """Test filter builds with error."""
    # Arrange
    platform = "android"
    filters = {"version": "1.0"}
    error_msg = "Filter error"
    build_manager.filter_builds.side_effect = Exception(error_msg)

    # Act
    result = build_controller.filter_builds(platform, filters)

    # Assert
    mock_message_box.critical.assert_called_once()
    assert error_msg in str(mock_message_box.critical.call_args[0][2])
    assert result == []


def test_progress_callback(build_controller, mock_progress_dialog):
    """Test progress callback updates dialog."""
    # Arrange
    progress = 50
    status = "Processing..."

    # Act
    build_controller._show_progress("Test", "Initializing...")
    if build_controller._progress_dialog:
        build_controller._progress_dialog.set_progress(progress, status)

    # Assert
    mock_progress_dialog.assert_called_once()
    mock_progress_dialog.return_value.set_progress.assert_called_once_with(
        progress, status
    )


def test_hide_progress(build_controller, mock_progress_dialog):
    """Test hiding progress dialog."""
    # Arrange
    build_controller._show_progress("Test", "Initializing...")

    # Act
    build_controller._hide_progress()

    # Assert
    mock_progress_dialog.return_value.close.assert_called_once()
    assert build_controller._progress_dialog is None


def test_show_error(build_controller, mock_message_box):
    """Test showing error message."""
    # Arrange
    title = "Error"
    message = "Test error"

    # Act
    build_controller._show_error(title, message)

    # Assert
    mock_message_box.critical.assert_called_once_with(None, title, message)
