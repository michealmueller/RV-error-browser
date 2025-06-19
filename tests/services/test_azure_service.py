"""
Unit tests for Azure service.
"""
import os
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime

from azure.core.exceptions import (
    ResourceNotFoundError,
    ResourceExistsError,
    ServiceRequestError,
    HttpResponseError
)

from services.azure_service import AzureService, AzureServiceError

@pytest.fixture
def azure_service():
    """Create an AzureService instance for testing."""
    service = AzureService()
    return service

@pytest.fixture
def mock_blob_service_client():
    """Create a mock BlobServiceClient."""
    with patch("azure.storage.blob.BlobServiceClient") as mock:
        yield mock

@pytest.fixture
def mock_credential():
    """Create a mock DefaultAzureCredential."""
    with patch("azure.identity.DefaultAzureCredential") as mock:
        yield mock

def test_initialize_success(azure_service, mock_credential, mock_blob_service_client):
    """Test successful initialization."""
    # Arrange
    container_name = "test-container"
    os.environ["AZURE_STORAGE_ACCOUNT"] = "testaccount"
    
    # Act
    azure_service.initialize(container_name)
    
    # Assert
    assert azure_service._container_name == container_name
    assert azure_service._credential is not None
    assert azure_service._blob_service_client is not None

def test_initialize_missing_account(azure_service):
    """Test initialization with missing storage account."""
    # Arrange
    container_name = "test-container"
    if "AZURE_STORAGE_ACCOUNT" in os.environ:
        del os.environ["AZURE_STORAGE_ACCOUNT"]
    
    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.initialize(container_name)
    assert "AZURE_STORAGE_ACCOUNT environment variable not set" in str(exc_info.value)

def test_initialize_credential_error(azure_service, mock_credential):
    """Test initialization with credential error."""
    # Arrange
    container_name = "test-container"
    os.environ["AZURE_STORAGE_ACCOUNT"] = "testaccount"
    mock_credential.side_effect = Exception("Credential error")
    
    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.initialize(container_name)
    assert "Failed to initialize Azure service" in str(exc_info.value)

def test_upload_file_success(azure_service, mock_blob_service_client):
    """Test successful file upload."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    file_path = "test.txt"
    blob_name = "test-blob"
    metadata = {"key": "value"}
    
    # Create test file
    with open(file_path, "w") as f:
        f.write("test content")
    
    try:
        # Act
        result = azure_service.upload_file(
            file_path=file_path,
            blob_name=blob_name,
            metadata=metadata
        )
        
        # Assert
        assert result is not None
        mock_blob_service_client.get_blob_client.assert_called_once()
        
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

def test_upload_file_not_found(azure_service):
    """Test upload with non-existent file."""
    # Arrange
    file_path = "nonexistent.txt"
    
    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.upload_file(file_path)
    assert "File not found" in str(exc_info.value)

def test_upload_file_azure_error(azure_service, mock_blob_service_client):
    """Test upload with Azure error."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    file_path = "test.txt"
    with open(file_path, "w") as f:
        f.write("test content")
    
    mock_blob_service_client.get_blob_client.return_value.upload_blob.side_effect = \
        ServiceRequestError("Network error")
    
    try:
        # Act & Assert
        with pytest.raises(AzureServiceError) as exc_info:
            azure_service.upload_file(file_path)
        assert "Network error" in str(exc_info.value)
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def test_download_file_success(azure_service, mock_blob_service_client):
    """Test successful file download."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    blob_name = "test-blob"
    destination_path = "downloaded.txt"
    
    # Mock blob properties and download stream
    mock_blob = Mock()
    mock_blob.size = 100
    mock_blob.download_blob.return_value.chunks.return_value = [b"test content"]
    
    mock_blob_service_client.get_blob_client.return_value.get_blob_properties.return_value = mock_blob
    
    try:
        # Act
        result = azure_service.download_file(
            blob_name=blob_name,
            destination_path=destination_path
        )
        
        # Assert
        assert result == destination_path
        assert os.path.exists(destination_path)
        
    finally:
        # Cleanup
        if os.path.exists(destination_path):
            os.remove(destination_path)

def test_download_file_not_found(azure_service, mock_blob_service_client):
    """Test download with non-existent blob."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    blob_name = "nonexistent-blob"
    destination_path = "downloaded.txt"
    
    mock_blob_service_client.get_blob_client.return_value.get_blob_properties.side_effect = \
        ResourceNotFoundError("Blob not found")
    
    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.download_file(blob_name, destination_path)
    assert "Blob not found" in str(exc_info.value)

def test_list_files_success(azure_service, mock_blob_service_client):
    """Test successful file listing."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    prefix = "test/"
    expected_files = ["test/file1.txt", "test/file2.txt"]
    
    mock_container = Mock()
    mock_container.list_blobs.return_value = [
        Mock(name=name) for name in expected_files
    ]
    mock_blob_service_client.get_container_client.return_value = mock_container
    
    # Act
    result = azure_service.list_files(prefix=prefix)
    
    # Assert
    assert result == expected_files

def test_list_files_container_not_found(azure_service, mock_blob_service_client):
    """Test listing files with non-existent container."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "nonexistent-container"
    
    mock_blob_service_client.get_container_client.return_value.list_blobs.side_effect = \
        ResourceNotFoundError("Container not found")
    
    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.list_files()
    assert "Container not found" in str(exc_info.value)

def test_get_file_metadata_success(azure_service, mock_blob_service_client):
    """Test successful metadata retrieval."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    blob_name = "test-blob"
    last_modified = datetime.now()
    metadata = {"version": "1.0"}
    
    mock_properties = Mock()
    mock_properties.size = 100
    mock_properties.last_modified = last_modified
    mock_properties.metadata = metadata
    
    mock_blob_service_client.get_blob_client.return_value.get_blob_properties.return_value = mock_properties
    
    # Act
    result = azure_service.get_file_metadata(blob_name)
    
    # Assert
    assert result["name"] == blob_name
    assert result["size"] == 100
    assert result["last_modified"] == last_modified
    assert result["metadata"] == metadata

def test_get_file_metadata_not_found(azure_service, mock_blob_service_client):
    """Test metadata retrieval for non-existent blob."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    blob_name = "nonexistent-blob"
    
    mock_blob_service_client.get_blob_client.return_value.get_blob_properties.side_effect = \
        ResourceNotFoundError("Blob not found")
    
    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.get_file_metadata(blob_name)
    assert "Blob not found" in str(exc_info.value)

def test_delete_file_success(azure_service, mock_blob_service_client):
    """Test successful file deletion."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    blob_name = "test-blob"
    
    # Act
    azure_service.delete_file(blob_name)
    
    # Assert
    mock_blob_service_client.get_blob_client.return_value.delete_blob.assert_called_once()

def test_delete_file_not_found(azure_service, mock_blob_service_client):
    """Test deletion of non-existent file."""
    # Arrange
    azure_service._blob_service_client = mock_blob_service_client
    azure_service._container_name = "test-container"
    
    blob_name = "nonexistent-blob"
    
    mock_blob_service_client.get_blob_client.return_value.delete_blob.side_effect = \
        ResourceNotFoundError("Blob not found")
    
    # Act & Assert
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.delete_file(blob_name)
    assert "Blob not found" in str(exc_info.value) 