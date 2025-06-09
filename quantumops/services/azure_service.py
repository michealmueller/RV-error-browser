"""
Azure service for handling Azure Storage operations.
"""
import logging
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import (
    AzureError,
    ResourceNotFoundError,
    ResourceExistsError,
    ServiceRequestError,
    HttpResponseError,
    ClientAuthenticationError
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
        self._max_retries = 3
        self._retry_delay = 1  # seconds
        
    def initialize(self, container_name: str) -> None:
        """Initialize the Azure service."""
        try:
            self._container_name = container_name
            self._credential = DefaultAzureCredential()
            self._blob_service_client = BlobServiceClient(
                account_url=self._get_storage_url(),
                credential=self._credential
            )
            logger.info("Azure service initialized successfully")
        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except Exception as e:
            error_msg = f"Failed to initialize Azure service: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
            
    def _get_storage_url(self) -> str:
        """Get the storage account URL from environment variables."""
        try:
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
            if not account_name:
                raise AzureServiceError("AZURE_STORAGE_ACCOUNT environment variable not set")
            return f"https://{account_name}.blob.core.windows.net"
        except Exception as e:
            error_msg = f"Error getting storage URL: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
            
    def upload_file(
        self,
        file_path: str,
        blob_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Upload a file to Azure Blob Storage."""
        if not self._blob_service_client:
            raise AzureServiceError("Azure service not initialized")
            
        if not os.path.exists(file_path):
            raise AzureServiceError(f"File not found: {file_path}")
            
        blob_name = blob_name or os.path.basename(file_path)
        metadata = metadata or {}
        
        try:
            # Get blob client
            blob_client = self._blob_service_client.get_blob_client(
                container=self._container_name,
                blob=blob_name
            )
            
            # Get file size for progress tracking
            file_size = os.path.getsize(file_path)
            uploaded_size = 0
            
            # Upload with progress tracking
            with open(file_path, "rb") as file:
                blob_client.upload_blob(
                    file,
                    overwrite=True,
                    metadata=metadata,
                    max_concurrency=4
                )
                
                # Update progress
                if progress_callback:
                    progress_callback(100, "Upload complete")
                    
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
        if not self._blob_service_client:
            raise AzureServiceError("Azure service not initialized")
            
        try:
            # Get blob client
            blob_client = self._blob_service_client.get_blob_client(
                container=self._container_name,
                blob=blob_name
            )
            
            # Get blob properties for size
            properties = blob_client.get_blob_properties()
            blob_size = properties.size
            
            # Create destination directory if it doesn't exist
            dir_name = os.path.dirname(destination_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
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
        if not self._blob_service_client:
            raise AzureServiceError("Azure service not initialized")
            
        try:
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
            
    def list_files(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files in the container."""
        if not self._blob_service_client:
            raise AzureServiceError("Azure service not initialized")
            
        try:
            container_client = self._blob_service_client.get_container_client(self._container_name)
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "metadata": blob.metadata
                })
                
            return files
            
        except ResourceNotFoundError:
            error_msg = f"Container not found: {self._container_name}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except Exception as e:
            error_msg = f"Error listing files: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
            
    def get_file_metadata(self, blob_name: str) -> Dict[str, Any]:
        """Get metadata for a file."""
        if not self._blob_service_client:
            raise AzureServiceError("Azure service not initialized")
        try:
            blob_client = self._blob_service_client.get_blob_client(
                container=self._container_name,
                blob=blob_name
            )
            properties = blob_client.get_blob_properties()
            return {
                "name": blob_name,
                "size": properties.size,
                "last_modified": properties.last_modified,
                "metadata": properties.metadata or {}
            }
        except ResourceNotFoundError:
            error_msg = f"Blob not found: {blob_name}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except Exception as e:
            error_msg = f"Error getting file metadata: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
            
    def update_file_metadata(self, blob_name: str, metadata: Dict[str, str]) -> None:
        """Update metadata for a file."""
        if not self._blob_service_client:
            raise AzureServiceError("Azure service not initialized")
            
        try:
            blob_client = self._blob_service_client.get_blob_client(
                container=self._container_name,
                blob=blob_name
            )
            blob_client.set_blob_metadata(metadata=metadata)
            logger.info(f"File metadata updated successfully: {blob_name}")
            
        except ResourceNotFoundError:
            error_msg = f"Blob not found: {blob_name}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
        except Exception as e:
            error_msg = f"Error updating file metadata: {str(e)}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg)
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self._blob_service_client = None
            self._credential = None
            self._container_name = None
            logger.info("Azure service cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 