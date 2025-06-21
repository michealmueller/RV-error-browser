"""
Build manager for handling mobile builds.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests
from PySide6.QtCore import QObject, Signal, Slot

from services.azure_service import AzureService, AzureServiceError
from services.eas_service import EasService

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

    def __init__(self, azure_service: AzureService):
        super().__init__()
        self._builds: Dict[str, List[Dict]] = {"android": [], "ios": []}
        self._download_dir = Path.home() / ".quantumops" / "downloads"
        self._download_dir.mkdir(parents=True, exist_ok=True)
        self._azure_service = azure_service
        self._eas_service = EasService()

    @Slot(str, bool)
    def fetch_builds(self, platform: str, force_refresh: bool = False):
        """Fetch builds from EAS."""
        if not force_refresh and self._builds.get(platform):
            self.builds_fetched.emit(self._builds[platform])
            self.build_list_updated.emit(self._builds[platform])
            return

        try:
            builds = self._eas_service.fetch_builds(platform)
            self._builds[platform] = builds
            self.builds_fetched.emit(builds)
            self.build_list_updated.emit(builds)
        except Exception as e:
            logger.error(f"Failed to fetch builds from EAS: {e}")
            self.error_occurred.emit(str(e))

    def get_builds(self, platform: str) -> List[Dict]:
        """Get the last fetched builds for a platform."""
        return self._builds.get(platform, [])

    def _get_filename(self, build: Dict, platform: str) -> str:
        """Construct the filename based on the new naming scheme."""
        build_id = build.get("id", "")
        profile = build.get("buildProfile", "development")
        version = build.get("appVersion", "0.0.0")
        version_code = build.get("appBuildVersion", "0")
        fingerprint = build_id[:7]
        extension = "apk" if platform == "android" else "ipa"

        return (
            f"{platform}-{profile}-v{version}-{version_code}-{fingerprint}.{extension}"
        )

    @Slot(str, str)
    def download_build(
        self, build_id: str, platform: str, progress_callback: Optional[Callable] = None
    ):
        """Download a build from its URL."""
        build = self._find_build(build_id, platform)
        if not build:
            self.error_occurred.emit(f"Build {build_id} not found.")
            return

        url = build.get("artifacts", {}).get("buildUrl")
        if not url:
            self.error_occurred.emit(f"No download URL for build {build_id}.")
            return

        filename = self._get_filename(build, platform)
        local_path = self._download_dir / filename

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    if total_size > 0:
                        downloaded_size += len(chunk)
                        progress = int((downloaded_size / total_size) * 100)
                        if progress_callback:
                            progress_callback(build_id, progress)

            logger.info(f"Build {build_id} downloaded to {local_path}")
            self.build_downloaded.emit(build_id, str(local_path))

        except requests.RequestException as e:
            logger.error(f"Failed to download build {build_id}: {e}")
            self.error_occurred.emit(str(e))

    @Slot(str, str)
    def push_to_azure(self, build_id: str, platform: str, local_path: str):
        """Upload a build to Azure."""
        try:
            build = self._find_build(build_id, platform)
            if not build:
                self.error_occurred.emit(f"Build {build_id} not found.")
                return

            filename = self._get_filename(build, platform)
            blob_name = f"{platform}-builds/{filename}"
            blob_url = self._azure_service.upload_file(
                file_path=local_path,
                blob_name=blob_name,
                metadata={
                    "build_id": build_id,
                    "uploaded_at": datetime.now().isoformat(),
                },
            )
            self.build_uploaded.emit(build_id, blob_url)
        except AzureServiceError as e:
            logger.error(f"Failed to upload build {build_id} to Azure: {e}")
            self.error_occurred.emit(str(e))

    def _find_build(self, build_id: str, platform: str) -> Optional[Dict]:
        """Find a build by its ID."""
        return next(
            (b for b in self._builds.get(platform, []) if b.get("id") == build_id), None
        )

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
                    build
                    for build in filtered_builds
                    if any(
                        search_text in str(value).lower() for value in build.values()
                    )
                ]

            # Apply version filter
            version = filters.get("version", "")
            if version:
                filtered_builds = [
                    build
                    for build in filtered_builds
                    if build.get("appVersion") == version
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
                (b for b in self._builds[platform] if b["id"] == build_id), None
            )
            if build:
                build["status"] = status
                self.build_status_changed.emit(build_id, status)
        except Exception as e:
            logger.error(f"Error updating build status: {e}")

    def get_local_path(self, build_id: str, platform: str) -> Optional[str]:
        """Get the local path for a specific build."""
        try:
            build = next(
                (b for b in self._builds[platform] if b["id"] == build_id), None
            )
            return build.get("local_path") if build else None
        except Exception as e:
            logger.error(f"Error getting local path for build {build_id}: {e}")
            return None

    def get_blob_url(self, build_id: str, platform: str) -> Optional[str]:
        """Get the blob URL for a specific build."""
        try:
            build = next(
                (b for b in self._builds[platform] if b["id"] == build_id), None
            )
            return build.get("blob_url") if build else None
        except Exception as e:
            logger.error(f"Error getting blob URL for build {build_id}: {e}")
            return None

    def refresh_builds(self, platform: str, force_refresh: bool = False) -> List[Dict]:
        """Refresh builds for a platform."""
        return self.fetch_builds(
            platform, force_refresh=True
        )  # Always force refresh when explicitly requested
