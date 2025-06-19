"""
Azure service for handling Azure Storage operations.
"""
import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import (
    AzureError,
    ResourceNotFoundError,
    ResourceExistsError,
    ServiceRequestError,
    HttpResponseError
)

logger = logging.getLogger(__name__)

class AzureServiceError(Exception):
    """Base exception for Azure service errors."""
    pass

class AzureService:
    """Service for handling Azure Storage operations."""
    
    def __init__(self):
        self._blob_service_client: Optional[BlobServiceClient] = None
        self._credential: Optional[DefaultAzureCredential] = None
        self._container_name: Optional[str] = None
        self._mock_mode = False
        
    def initialize(self, container_name: str = None) -> None:
        """Initialize the Azure service."""
        try:
            # Use container name from parameter or environment variable
            self._container_name = container_name or os.getenv("AZURE_STORAGE_CONTAINER", "mobile-builds")
            
            # Check if Azure configuration is available
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
            if not account_name:
                logger.warning("AZURE_STORAGE_ACCOUNT environment variable not set. Running in mock mode.")
                self._mock_mode = True
                return
                
            self._credential = DefaultAzureCredential()
            self._blob_service_client = BlobServiceClient(
                account_url=self._get_storage_url(),
                credential=self._credential
            )
            logger.info("Azure service initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize Azure service: {str(e)}"
            logger.error(error_msg)
            logger.warning("Running in mock mode due to initialization failure.")
            self._mock_mode = True
            
    def _get_storage_url(self) -> str:
        """Get the storage account URL from environment variables."""
        account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
        if not account_name:
            raise AzureServiceError("AZURE_STORAGE_ACCOUNT environment variable not set")
        return f"https://{account_name}.blob.core.windows.net"
        
    def upload_file(
        self,
        file_path: str,
        blob_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Upload a file to Azure Blob Storage."""
        if self._mock_mode:
            logger.info(f"Mock mode: Simulating upload of {file_path}")
            if progress_callback:
                progress_callback(100, "Mock upload completed")
            return f"mock://{self._container_name}/{blob_name or 'mock-blob'}"
            
        try:
            if not self._blob_service_client:
                raise AzureServiceError("Azure service not initialized")
                
            file_path = Path(file_path)
            if not file_path.exists():
                raise AzureServiceError(f"File not found: {file_path}")
                
            # Generate blob name if not provided
            if not blob_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob_name = f"{timestamp}_{file_path.name}"
                
            # Get blob client
            blob_client = self._blob_service_client.get_blob_client(
                container=self._container_name,
                blob=blob_name
            )
            
            # Upload file with progress tracking
            with open(file_path, "rb") as data:
                file_size = file_path.stat().st_size
                uploaded_size = 0
                
                # Upload in chunks for progress tracking
                chunk_size = 4 * 1024 * 1024  # 4MB chunks
                while True:
                    chunk = data.read(chunk_size)
                    if not chunk:
                        break
                        
                    blob_client.upload_blob(
                        chunk,
                        overwrite=True,
                        metadata=metadata
                    )
                    
                    uploaded_size += len(chunk)
                    if progress_callback:
                        progress = int((uploaded_size / file_size) * 100)
                        progress_callback(progress, f"Uploading: {progress}%")
                        
            logger.info(f"File uploaded successfully: {blob_name}")
            return blob_client.url
            
        except ResourceExistsError:
            error_msg = f"Blob already exists: {blob_name}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except ResourceNotFoundError:
            error_msg = f"Container not found: {self._container_name}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except ServiceRequestError as e:
            error_msg = f"Network error during upload: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except HttpResponseError as e:
            error_msg = f"Azure API error during upload: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
            
    def download_file(
        self,
        blob_name: str,
        destination_path: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Download a file from Azure Blob Storage."""
        if self._mock_mode:
            logger.info(f"Mock mode: Simulating download of {blob_name}")
            # Create a mock file
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            with open(destination_path, 'w') as f:
                f.write(f"Mock content for {blob_name}")
            if progress_callback:
                progress_callback(100, "Mock download completed")
            return destination_path
            
        try:
            if not self._blob_service_client:
                raise AzureServiceError("Azure service not initialized")
                
            # Get blob client
            blob_client = self._blob_service_client.get_blob_client(
                container=self._container_name,
                blob=blob_name
            )
            
            # Get blob properties for size
            properties = blob_client.get_blob_properties()
            blob_size = properties.size
            
            # Download with progress tracking
            with open(destination_path, "wb") as file:
                downloaded_size = 0
                chunk_size = 4 * 1024 * 1024  # 4MB chunks
                
                download_stream = blob_client.download_blob()
                for chunk in download_stream.chunks():
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    if progress_callback:
                        progress = int((downloaded_size / blob_size) * 100)
                        progress_callback(progress, f"Downloading: {progress}%")
                        
            logger.info(f"File downloaded successfully: {destination_path}")
            return destination_path
            
        except ResourceNotFoundError:
            error_msg = f"Blob not found: {blob_name}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except ServiceRequestError as e:
            error_msg = f"Network error during download: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except HttpResponseError as e:
            error_msg = f"Azure API error during download: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during download: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
            
    def delete_file(self, blob_name: str) -> None:
        """Delete a file from Azure Blob Storage."""
        try:
            if not self._blob_service_client:
                raise AzureServiceError("Azure service not initialized")
                
            blob_client = self._blob_service_client.get_blob_client(
                container=self._container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"File deleted successfully: {blob_name}")
            
        except ResourceNotFoundError:
            error_msg = f"Blob not found: {blob_name}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except Exception as e:
            error_msg = f"Error deleting file: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
            
    def list_files(self, prefix: Optional[str] = None) -> list:
        """List files in the container."""
        if self._mock_mode:
            logger.info(f"Mock mode: Simulating list files with prefix {prefix}")
            # Return mock file list
            mock_files = [
                f"{prefix or 'android'}/build_001.apk",
                f"{prefix or 'android'}/build_002.apk",
                f"{prefix or 'ios'}/build_001.ipa",
                f"{prefix or 'ios'}/build_002.ipa"
            ]
            return [f for f in mock_files if not prefix or f.startswith(prefix)]
            
        try:
            if not self._blob_service_client:
                raise AzureServiceError("Azure service not initialized")
                
            container_client = self._blob_service_client.get_container_client(self._container_name)
            blobs = container_client.list_blobs(name_starts_with=prefix)
            return [blob.name for blob in blobs]
            
        except Exception as e:
            logger.warning(f"Azure operation failed, falling back to mock mode: {e}")
            self._mock_mode = True
            return self.list_files(prefix)  # Recursive call with mock mode
            
    def get_file_metadata(self, blob_name: str) -> Dict[str, Any]:
        """Get metadata for a file."""
        if self._mock_mode:
            logger.info(f"Mock mode: Simulating metadata for {blob_name}")
            return {
                "name": blob_name,
                "size": 1024 * 1024,  # 1MB mock size
                "last_modified": datetime.now(),
                "metadata": {
                    "version": "1.0.0",
                    "platform": "android" if blob_name.endswith(".apk") else "ios",
                    "build_id": blob_name.split("/")[-1].split(".")[0]
                }
            }
            
        try:
            if not self._blob_service_client:
                raise AzureServiceError("Azure service not initialized")
                
            blob_client = self._blob_service_client.get_blob_client(
                container=self._container_name,
                blob=blob_name
            )
            properties = blob_client.get_blob_properties()
            
            return {
                "name": blob_name,
                "size": properties.size,
                "last_modified": properties.last_modified,
                "metadata": properties.metadata
            }
            
        except ResourceNotFoundError:
            error_msg = f"Blob not found: {blob_name}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except Exception as e:
            error_msg = f"Error getting file metadata: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg) 