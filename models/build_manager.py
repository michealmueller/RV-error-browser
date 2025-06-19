"""
Build manager for handling mobile builds.
"""
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from services.azure_service import AzureService, AzureServiceError

logger = logging.getLogger(__name__)

class BuildManager(QObject):
    """Manager for handling mobile builds."""
    builds_fetched = Signal(list)  # List of build metadata
    build_downloaded = Signal(str, str)  # build_id, local_path
    build_uploaded = Signal(str, str)  # build_id, blob_url
    error_occurred = Signal(str)  # Error message
    upload_retry = Signal(str, str, int)  # build_id, local_path, attempt
    build_list_updated = Signal(list)  # List of build metadata
    build_status_changed = Signal(str, str)  # build_id, new_status

    def __init__(self):
        super().__init__()
        self._builds: Dict[str, List[Dict]] = {
            "android": [],
            "ios": []
        }
        self._download_dir = Path.home() / ".quantumops" / "downloads"
        self._download_dir.mkdir(parents=True, exist_ok=True)
        self._azure_service = AzureService()
        
    def initialize_azure(self, container_name: str) -> None:
        """Initialize Azure service."""
        try:
            self._azure_service.initialize(container_name)
        except AzureServiceError as e:
            logger.error(f"Failed to initialize Azure service: {e}")
            raise
            
    def download_build(
        self,
        build_id: str,
        platform: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """Download a build and return local path."""
        try:
            build = next(
                (b for b in self._builds[platform] if b["id"] == build_id),
                None
            )
            if not build:
                raise ValueError(f"Build {build_id} not found")
                
            # Create platform-specific directory
            platform_dir = self._download_dir / platform
            platform_dir.mkdir(exist_ok=True)
            
            # Determine file extension
            ext = ".apk" if platform == "android" else ".ipa"
            local_path = platform_dir / f"{build_id}{ext}"
            
            # Download from Azure
            self._azure_service.download_file(
                blob_name=build_id,
                destination_path=str(local_path),
                progress_callback=progress_callback
            )
            
            # Update build status
            build["status"] = "downloaded"
            build["local_path"] = str(local_path)
            self.build_downloaded.emit(build_id, str(local_path))
            self.build_status_changed.emit(build_id, "downloaded")
            
            return str(local_path)
            
        except AzureServiceError as e:
            logger.error(f"Azure error downloading build {build_id}: {e}")
            self.error_occurred.emit(str(e))
            raise
        except Exception as e:
            logger.error(f"Error downloading build {build_id}: {e}")
            self.error_occurred.emit(str(e))
            raise
            
    def upload_build(
        self,
        build_id: str,
        local_path: str,
        platform: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """Upload a build and return blob URL."""
        try:
            build = next(
                (b for b in self._builds[platform] if b["id"] == build_id),
                None
            )
            if not build:
                raise ValueError(f"Build {build_id} not found")
                
            if not Path(local_path).exists():
                raise ValueError(f"Build file not found: {local_path}")
                
            # Upload to Azure
            blob_url = self._azure_service.upload_file(
                file_path=local_path,
                blob_name=build_id,
                metadata={
                    "platform": platform,
                    "build_id": build_id,
                    "upload_date": datetime.now().isoformat()
                },
                progress_callback=progress_callback
            )
            
            # Update build status
            build["status"] = "uploaded"
            build["blob_url"] = blob_url
            self.build_uploaded.emit(build_id, blob_url)
            self.build_status_changed.emit(build_id, "uploaded")
            
            return blob_url
            
        except AzureServiceError as e:
            logger.error(f"Azure error uploading build {build_id}: {e}")
            self.error_occurred.emit(str(e))
            raise
        except Exception as e:
            logger.error(f"Error uploading build {build_id}: {e}")
            self.error_occurred.emit(str(e))
            raise
            
    def fetch_builds(
        self,
        platform: str,
        force_refresh: bool = False,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> List[Dict]:
        """Fetch builds for a platform."""
        try:
            if not force_refresh and self._builds[platform]:
                self.builds_fetched.emit(self._builds[platform])
                self.build_list_updated.emit(self._builds[platform])
                return self._builds[platform]
                
            if progress_callback:
                progress_callback(0, "Fetching builds...")
                
            # List files in Azure container
            files = self._azure_service.list_files(prefix=platform)
            
            # Get metadata for each file
            builds = []
            for i, file_name in enumerate(files):
                if progress_callback:
                    progress = int((i / len(files)) * 100)
                    progress_callback(progress, f"Processing build {i+1}/{len(files)}")
                    
                metadata = self._azure_service.get_file_metadata(file_name)
                builds.append({
                    "id": file_name,
                    "version": metadata["metadata"].get("version", "unknown"),
                    "status": "available",
                    "size": metadata["size"],
                    "date": metadata["last_modified"].isoformat()
                })
                
            if progress_callback:
                progress_callback(100, "Builds fetched successfully")
                
            self._builds[platform] = builds
            self.builds_fetched.emit(builds)
            self.build_list_updated.emit(builds)
            return builds
            
        except AzureServiceError as e:
            logger.error(f"Azure error fetching builds: {e}")
            self.error_occurred.emit(str(e))
            raise
        except Exception as e:
            logger.error(f"Error fetching builds: {e}")
            self.error_occurred.emit(str(e))
            raise
            
    def filter_builds(self, platform: str, filters: Dict) -> List[Dict]:
        """Filter builds based on criteria."""
        try:
            builds = self._builds[platform]
            if not builds:
                return []
                
            filtered_builds = builds.copy()
            
            # Apply search filter
            search_text = filters.get("search", "").lower()
            if search_text:
                filtered_builds = [
                    build for build in filtered_builds
                    if any(
                        search_text in str(value).lower()
                        for value in build.values()
                    )
                ]
            # Emit updated list
            self.build_list_updated.emit(filtered_builds)
            return filtered_builds
            
        except Exception as e:
            logger.error(f"Error filtering builds: {e}")
            self.error_occurred.emit(str(e))
            raise 

    def update_build_status(self, build_id: str, platform: str, status: str):
        """Update the status of a specific build and emit signal."""
        try:
            build = next(
                (b for b in self._builds[platform] if b["id"] == build_id),
                None
            )
            if build:
                build["status"] = status
                self.build_status_changed.emit(build_id, status)
        except Exception as e:
            logger.error(f"Error updating build status: {e}")
            
    def get_builds(self, platform: str = None) -> List[Dict]:
        """Get builds for a specific platform or all platforms."""
        if platform:
            return self._builds.get(platform, [])
        else:
            # Return all builds from all platforms
            all_builds = []
            for platform_builds in self._builds.values():
                all_builds.extend(platform_builds)
            return all_builds
            
    def get_local_path(self, build_id: str, platform: str) -> Optional[str]:
        """Get the local path for a specific build."""
        try:
            build = next(
                (b for b in self._builds[platform] if b["id"] == build_id),
                None
            )
            return build.get("local_path") if build else None
        except Exception as e:
            logger.error(f"Error getting local path for build {build_id}: {e}")
            return None
            
    def get_blob_url(self, build_id: str, platform: str) -> Optional[str]:
        """Get the blob URL for a specific build."""
        try:
            build = next(
                (b for b in self._builds[platform] if b["id"] == build_id),
                None
            )
            return build.get("blob_url") if build else None
        except Exception as e:
            logger.error(f"Error getting blob URL for build {build_id}: {e}")
            return None 