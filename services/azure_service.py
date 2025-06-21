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
    """Custom exception for Azure service errors."""
    pass

class AzureService:
    """Service for interacting with Azure Storage."""
    
    def __init__(self):
        """Initialize AzureService."""
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
            account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
            if account_name and account_key:
                connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
            else:
                raise ValueError("Missing required Azure credentials. Either AZURE_STORAGE_CONNECTION_STRING or both AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_ACCOUNT_KEY must be set.")

        container_name = os.getenv("AZURE_STORAGE_CONTAINER")
        if not container_name:
            raise ValueError("Missing required Azure container name")
            
        self._blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self._container_client = self._blob_service_client.get_container_client(container_name)
        
    def upload_file(self, file_path: str, blob_name: str, metadata: dict = None) -> str:
        """Upload a file to Azure Blob Storage."""
        try:
            blob_client = self._container_client.get_blob_client(blob=blob_name)
            
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, metadata=metadata, overwrite=True)
            
            logger.info(f"Successfully uploaded {file_path} to {blob_name}")
            return blob_client.url
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to Azure: {str(e)}")
            raise AzureServiceError(f"Failed to upload file to Azure: {str(e)}")
        
    def download_file(self, blob_name: str, download_path: str) -> None:
        """Download a file from Azure Blob Storage."""
        try:
            blob_client = self._container_client.get_blob_client(blob=blob_name)
            with open(download_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            logger.info(f"Successfully downloaded {blob_name} to {download_path}")
        except AzureError as e:
            logger.error(f"Failed to download file {blob_name} from Azure: {e}")
            raise AzureServiceError(f"Failed to download file from Azure: {e}")
            
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