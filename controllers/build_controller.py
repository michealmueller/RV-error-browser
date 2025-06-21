"""
Build controller for coordinating between model and view.
"""
import logging
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QMessageBox
from models.build_manager import BuildManager
from views.build_view import BuildView
from services.azure_service import AzureServiceError

logger = logging.getLogger(__name__)

class BuildController(QObject):
    """Controller for build operations."""
    
    # Signals
    builds_fetched = Signal(list)
    build_downloaded = Signal(str, str)
    build_uploaded = Signal(str, str)
    error_occurred = Signal(str)
    
    def __init__(self, model: BuildManager, view: BuildView):
        super().__init__()
        self._model = model
        self._view = view
        self._upload_after_download_queue = set()
        
        # Connect model signals
        self._model.builds_fetched.connect(self._view.update_builds)
        self._model.build_downloaded.connect(self._on_build_downloaded)
        self._model.build_uploaded.connect(self._on_build_uploaded)
        self._model.build_status_changed.connect(self._view.update_build_status)
        self._model.error_occurred.connect(self._view.show_error)
        self._model.error_occurred.connect(self.error_occurred)

        # Connect view signals
        self._view.fetch_requested.connect(self.fetch_builds)
        self._view.download_requested.connect(self.download_build)
        self._view.push_to_azure_requested.connect(self._on_push_to_azure_requested)
        
    @Slot()
    def fetch_builds(self):
        """Fetch builds for the view's platform."""
        self._view.show_loading()
        self._model.fetch_builds(self._view.platform)
        
    @Slot(str)
    def download_build(self, build_id: str):
        """Download a build."""
        self._view.show_download_progress(build_id)
        self._model.download_build(
            build_id, self._view.platform, self._view.update_download_progress
        )
        
    @Slot(str, str)
    def _on_build_downloaded(self, build_id: str, local_path: str):
        """Handle successful download."""
        self._view.hide_download_progress(build_id)
        QMessageBox.information(
            self._view,
            "Download Complete",
            f"Build {build_id} downloaded to:\\n{local_path}"
        )
        self._model.update_build_status(build_id, self._view.platform, "Downloaded")

        # If this download was triggered by a push request, start the upload
        if build_id in self._upload_after_download_queue:
            self._upload_after_download_queue.remove(build_id)
            self._model.push_to_azure(build_id, self._view.platform, local_path)

    @Slot(str)
    def _on_push_to_azure_requested(self, build_id: str):
        """Handle request to push a build to azure."""
        build = self._model._find_build(build_id, self._view.platform)
        if not build:
            self.error_occurred.emit(f"Build {build_id} not found.")
            return

        filename = self._model._get_filename(build, self._view.platform)
        local_path = self._model._download_dir / filename
        
        if not local_path.exists():
            self._upload_after_download_queue.add(build_id)
            self.download_build(build_id)
            QMessageBox.information(self._view, "Download Started", "Build must be downloaded first. Download has been initiated and will be uploaded automatically.")
            return

        self._model.push_to_azure(build_id, self._view.platform, str(local_path))

    @Slot(str, str)
    def _on_build_uploaded(self, build_id: str, blob_url: str):
        """Handle successful upload."""
        QMessageBox.information(
            self._view,
            "Upload Complete",
            f"Build {build_id} uploaded to Azure."
        )
        self._model.update_build_status(build_id, self._view.platform, "Uploaded")
        self.error_occurred.emit(f"Build {build_id} uploaded to: {blob_url}")

    def cleanup(self):
        """Clean up resources."""
        logger.info(f"Build controller cleaned up for {self._view.platform}") 