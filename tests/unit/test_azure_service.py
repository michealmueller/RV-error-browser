import pytest
from unittest.mock import Mock, patch, MagicMock, ANY
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from quantumops.services.azure_service import AzureService, AzureServiceError
import time
import os
import io

@pytest.fixture
def mock_blob_service():
    """Create a mock BlobServiceClient."""
    return Mock(spec=BlobServiceClient)

@pytest.fixture
def mock_container():
    """Create a mock ContainerClient."""
    return Mock(spec=ContainerClient)

@pytest.fixture
def mock_blob():
    """Create a mock BlobClient."""
    return Mock(spec=BlobClient)

@pytest.fixture
def azure_service():
    """Create an AzureService instance with mocked dependencies and initialized container."""
    with patch('azure.identity.DefaultAzureCredential') as mock_credential, \
         patch('azure.storage.blob.BlobServiceClient') as mock_blob_service_class, \
         patch.dict(os.environ, {'AZURE_STORAGE_ACCOUNT': 'testaccount'}):
        # Create mock objects
        mock_blob_service = Mock(spec=BlobServiceClient)
        mock_container = Mock(spec=ContainerClient)
        mock_blob = Mock(spec=BlobClient)
        
        # Patch get_container_client and get_blob_client to always return our mocks
        mock_blob_service.get_container_client.return_value = mock_container
        mock_blob_service.get_blob_client.return_value = mock_blob
        mock_container.get_blob_client.return_value = mock_blob
        
        # Patch list_blobs to return a real list of objects with real attributes
        class BlobObj:
            def __init__(self):
                self.name = "test.txt"
                self.size = 1000
                self.last_modified = "2024-01-01"
                self.metadata = {"key": "value"}
        mock_container.list_blobs.return_value = [BlobObj()]
        # Patch download_blob().chunks() to return a real list
        mock_blob.download_blob.return_value.chunks.return_value = [b"test data"]
        # Patch get_blob_properties to return a real object with attributes
        class BlobProps:
            size = 1000
            last_modified = "2024-01-01"
            metadata = {"key": "value"}
        mock_blob.get_blob_properties.return_value = BlobProps()
        # Patch set_blob_metadata to do nothing
        mock_blob.set_blob_metadata.return_value = None
        # Patch delete_blob to do nothing
        mock_blob.delete_blob.return_value = None
        # Patch upload_blob to do nothing
        mock_blob.upload_blob.return_value = None
        
        # Create and initialize service
        service = AzureService()
        service.initialize(container_name="test_container")
        
        # Store mocks for test access
        service._mock_blob_service = mock_blob_service
        service._mock_container = mock_container
        service._mock_blob = mock_blob
        
        # Ensure the service uses our mocked blob client
        service._blob_service_client = mock_blob_service
        
        return service

def test_initialize_success():
    """Test successful initialization."""
    with patch('azure.identity.DefaultAzureCredential') as mock_credential, \
         patch('azure.storage.blob.BlobServiceClient') as mock_blob_service_class, \
         patch.dict(os.environ, {'AZURE_STORAGE_ACCOUNT': 'testaccount'}):
        mock_blob_service = Mock(spec=BlobServiceClient)
        mock_blob_service_class.return_value = mock_blob_service
        service = AzureService()
        service.initialize(container_name="test_container")
        assert service._blob_service_client is not None
        assert service._credential is not None
        assert service._container_name == "test_container"

def test_initialize_container_not_exists():
    """Test initialization with non-existent container."""
    with patch('azure.identity.DefaultAzureCredential') as mock_credential, \
         patch('azure.storage.blob.BlobServiceClient.__init__', side_effect=ResourceNotFoundError("Container not found")), \
         patch.dict(os.environ, {'AZURE_STORAGE_ACCOUNT': 'testaccount'}):
        service = AzureService()
        with pytest.raises(AzureServiceError) as exc_info:
            service.initialize(container_name="test_container")
        assert "Failed to initialize Azure service" in str(exc_info.value)

def test_initialize_auth_error():
    """Test initialization with authentication error."""
    with patch('azure.identity.DefaultAzureCredential') as mock_credential, \
         patch('azure.storage.blob.BlobServiceClient.__init__', side_effect=ClientAuthenticationError("Invalid credentials")), \
         patch.dict(os.environ, {'AZURE_STORAGE_ACCOUNT': 'testaccount'}):
        service = AzureService()
        with pytest.raises(AzureServiceError) as exc_info:
            service.initialize(container_name="test_container")
        assert "Authentication failed" in str(exc_info.value)

def test_upload_file_success(azure_service):
    """Test successful file upload."""
    mock_blob = azure_service._mock_blob
    with patch('builtins.open', MagicMock(return_value=io.BytesIO(b"test data"))), \
         patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1000):
        result = azure_service.upload_file("test.txt", "test.txt")
        assert result is not None
        mock_blob.upload_blob.assert_called_once()

def test_upload_file_not_found(azure_service):
    """Test upload with non-existent file."""
    with patch('os.path.exists', return_value=False):
        with pytest.raises(AzureServiceError) as exc_info:
            azure_service.upload_file("nonexistent.txt")
        assert "File not found" in str(exc_info.value)

def test_download_file_success(azure_service):
    """Test successful file download."""
    mock_blob = azure_service._mock_blob
    with patch('builtins.open', MagicMock()) as mock_open, \
         patch('os.makedirs'):
        result = azure_service.download_file("test.txt", "test.txt")
        assert result == "test.txt"
        mock_open.assert_called_once()

def test_download_file_not_found(azure_service):
    """Test download with non-existent blob."""
    mock_blob = azure_service._mock_blob
    mock_blob.get_blob_properties.side_effect = ResourceNotFoundError("Blob not found")
    with patch('os.makedirs'), patch('builtins.open', MagicMock()):
        with pytest.raises(AzureServiceError) as exc_info:
            azure_service.download_file("test.txt", "test.txt")
        assert "Blob not found" in str(exc_info.value)
    # Reset side effect for other tests
    mock_blob.get_blob_properties.side_effect = None

def test_delete_file_success(azure_service):
    """Test successful file deletion."""
    mock_blob = azure_service._mock_blob
    azure_service.delete_file("test.txt")
    mock_blob.delete_blob.assert_called_once()

def test_delete_file_not_found(azure_service):
    """Test deletion with non-existent blob."""
    mock_blob = azure_service._mock_blob
    mock_blob.delete_blob.side_effect = ResourceNotFoundError("Blob not found")
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.delete_file("test.txt")
    assert "Blob not found" in str(exc_info.value)
    # Reset side effect for other tests
    mock_blob.delete_blob.side_effect = None

def test_list_files_success(azure_service):
    """Test successful file listing."""
    files = azure_service.list_files()
    assert len(files) == 1
    assert files[0]["name"] == "test.txt"

def test_list_files_error(azure_service):
    """Test file listing with error."""
    mock_container = azure_service._mock_container
    mock_container.list_blobs.side_effect = Exception("Error listing files")
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.list_files()
    assert "Error listing files" in str(exc_info.value)
    # Reset side effect for other tests
    mock_container.list_blobs.side_effect = None

def test_get_file_metadata_success(azure_service):
    """Test successful metadata retrieval."""
    metadata = azure_service.get_file_metadata("test.txt")
    assert metadata["size"] == 1000
    assert metadata["last_modified"] == "2024-01-01"
    assert metadata["metadata"] == {"key": "value"}

def test_get_file_metadata_not_found(azure_service):
    """Test metadata retrieval for non-existent blob."""
    mock_blob = azure_service._mock_blob
    mock_blob.get_blob_properties.side_effect = ResourceNotFoundError("Blob not found")
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.get_file_metadata("test.txt")
    assert "Blob not found" in str(exc_info.value)
    # Reset side effect for other tests
    mock_blob.get_blob_properties.side_effect = None

def test_update_file_metadata_success(azure_service):
    """Test successful metadata update."""
    mock_blob = azure_service._mock_blob
    azure_service.update_file_metadata("test.txt", {"key": "value"})
    mock_blob.set_blob_metadata.assert_called_once_with(metadata={"key": "value"})

def test_update_file_metadata_not_found(azure_service):
    """Test metadata update for non-existent blob."""
    mock_blob = azure_service._mock_blob
    mock_blob.set_blob_metadata.side_effect = ResourceNotFoundError("Blob not found")
    with pytest.raises(AzureServiceError) as exc_info:
        azure_service.update_file_metadata("test.txt", {"key": "value"})
    assert "Blob not found" in str(exc_info.value)
    # Reset side effect for other tests
    mock_blob.set_blob_metadata.side_effect = None

def test_cleanup(azure_service):
    """Test cleanup method."""
    azure_service.cleanup()
    assert azure_service._blob_service_client is None
    assert azure_service._credential is None 