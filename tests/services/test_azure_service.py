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

from quantumops.services.azure_service import AzureService, AzureServiceError

@pytest.fixture
def mock_credential():
    """Create a mock Azure credential."""
    with patch("azure.identity.DefaultAzureCredential") as mock:
        mock_cred = Mock()
        mock.return_value = mock_cred
        yield mock_cred

@pytest.fixture
def mock_blob_service_client():
    """Create a mock blob service client."""
    with patch("azure.storage.blob.BlobServiceClient") as mock:
        mock_client = Mock()
        mock_container = Mock()
        mock_blob = Mock()
        
        # Set up the mock chain
        mock_client.get_container_client.return_value = mock_container
        mock_container.get_blob_client.return_value = mock_blob
        
        # Set up blob operations
        mock_blob.upload_blob = Mock()
        mock_blob.download_blob = Mock()
        mock_blob.get_blob_properties = Mock()
        
        # Set up container operations
        mock_container.list_blobs = Mock()
        mock_container.get_blob_client = Mock(return_value=mock_blob)
        
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def azure_service(mock_credential, mock_blob_service_client):
    """Create an AzureService instance with mocked dependencies."""
    return AzureService()

def test_initialize_success(azure_service, mock_credential, mock_blob_service_client):
    """Test successful Azure service initialization."""
    azure_service.initialize("test-container")
    
    assert azure_service._credential is not None
    assert azure_service._blob_service_client is not None
    mock_blob_service_client.get_container_client.assert_called_once_with("test-container")

def test_initialize_error(azure_service, mock_credential, mock_blob_service_client):
    """Test Azure service initialization error."""
    mock_blob_service_client.get_container_client.side_effect = Exception("Connection error")
    
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.initialize("test-container")
    
    assert "Failed to initialize Azure service" in str(exc_info.value)

def test_upload_file_success(azure_service, mock_blob_service_client):
    """Test successful file upload."""
    azure_service.initialize("test-container")
    test_file = Path("/tmp/test.txt")
    test_file.write_text("test content")
    
    azure_service.upload_file(test_file, "test.txt")
    
    mock_blob = mock_blob_service_client.get_container_client().get_blob_client()
    mock_blob.upload_blob.assert_called_once()
    test_file.unlink()

def test_upload_file_not_found(azure_service):
    """Test file upload with non-existent file."""
    azure_service.initialize("test-container")
    
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.upload_file(Path("/tmp/nonexistent.txt"), "test.txt")
    
    assert "Failed to upload file" in str(exc_info.value)

def test_download_file_success(azure_service, mock_blob_service_client):
    """Test successful file download."""
    azure_service.initialize("test-container")
    test_file = Path("/tmp/test.txt")
    
    azure_service.download_file("test.txt", test_file)
    
    mock_blob = mock_blob_service_client.get_container_client().get_blob_client()
    mock_blob.download_blob.assert_called_once()
    test_file.unlink()

def test_download_file_not_found(azure_service, mock_blob_service_client):
    """Test file download with non-existent blob."""
    azure_service.initialize("test-container")
    mock_blob = mock_blob_service_client.get_container_client().get_blob_client()
    mock_blob.download_blob.side_effect = Exception("Blob not found")
    
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.download_file("nonexistent.txt", Path("/tmp/test.txt"))
    
    assert "Failed to download file" in str(exc_info.value)

def test_list_files_success(azure_service, mock_blob_service_client):
    """Test successful file listing."""
    azure_service.initialize("test-container")
    mock_blobs = [
        Mock(name="file1.txt"),
        Mock(name="file2.txt")
    ]
    mock_blob_service_client.get_container_client().list_blobs.return_value = mock_blobs
    
    files = azure_service.list_files()
    
    assert len(files) == 2
    assert "file1.txt" in files
    assert "file2.txt" in files

def test_list_files_error(azure_service, mock_blob_service_client):
    """Test file listing error."""
    azure_service.initialize("test-container")
    mock_blob_service_client.get_container_client().list_blobs.side_effect = Exception("List error")
    
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.list_files()
    
    assert "Failed to list files" in str(exc_info.value)

def test_get_file_metadata_success(azure_service, mock_blob_service_client):
    """Test successful metadata retrieval."""
    azure_service.initialize("test-container")
    mock_properties = Mock(
        size=1024,
        last_modified="2024-01-01T00:00:00Z",
        metadata={"version": "1.0.0"}
    )
    mock_blob = mock_blob_service_client.get_container_client().get_blob_client()
    mock_blob.get_blob_properties.return_value = mock_properties
    
    metadata = azure_service.get_file_metadata("test.txt")
    
    assert metadata["size"] == 1024
    assert metadata["last_modified"] == "2024-01-01T00:00:00Z"
    assert metadata["version"] == "1.0.0"

def test_get_file_metadata_not_found(azure_service, mock_blob_service_client):
    """Test metadata retrieval for non-existent file."""
    azure_service.initialize("test-container")
    mock_blob = mock_blob_service_client.get_container_client().get_blob_client()
    mock_blob.get_blob_properties.side_effect = Exception("Blob not found")
    
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.get_file_metadata("nonexistent.txt")
    
    assert "Failed to get file metadata" in str(exc_info.value)

def test_cleanup(azure_service, mock_blob_service_client):
    """Test service cleanup."""
    azure_service.initialize("test-container")
    azure_service.cleanup()
    
    assert azure_service._credential is None
    assert azure_service._blob_service_client is None 