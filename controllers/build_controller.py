"""
Build controller for coordinating between model and view.
"""
import logging
import subprocess
import os
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import QMessageBox
from models.build_manager import BuildManager
from views.build_view import BuildView
from views.progress_dialog import ProgressDialog
from services.azure_service import AzureServiceError

logger = logging.getLogger(__name__)

class BuildController(QObject):
    """Controller for build operations."""
    
    # Signals
    builds_fetched = Signal(list)  # List of build metadata
    build_downloaded = Signal(str, str)  # build_id, local_path
    build_uploaded = Signal(str, str)  # build_id, blob_url
    error_occurred = Signal(str)  # Error message
    upload_retry = Signal(str, str, int)  # build_id, local_path, attempt
    
    # Progress signals
    download_started = Signal(str)  # build_id
    download_progress = Signal(str, int)  # build_id, progress
    upload_started = Signal(str)  # build_id
    upload_progress = Signal(str, int)  # build_id, progress
    
    def __init__(self, model: BuildManager, view: BuildView):
        super().__init__()
        self._model = model
        self._view = view
        self._progress_dialog: Optional[ProgressDialog] = None
        
        # Connect model signals
        self._model.builds_fetched.connect(self.builds_fetched)
        self._model.build_downloaded.connect(self.build_downloaded)
        self._model.build_uploaded.connect(self.build_uploaded)
        self._model.error_occurred.connect(self.error_occurred)
        self._model.upload_retry.connect(self.upload_retry)
        
        # Connect view signals
        self._view.fetch_requested.connect(self._model.fetch_builds)
        self._view.download_requested.connect(self._model.download_build)
        self._view.upload_requested.connect(self._handle_upload_request)
        self._view.install_requested.connect(self._handle_install_request)
        self._view.share_requested.connect(self._handle_share_request)
        
        logger.info(f"Build controller initialized for {view.platform}")
        
    def _handle_build_downloaded(self, build_id: str, local_path: str):
        """Handle build download completion."""
        # Update UI
        self._view.update_build_status(build_id, "downloaded")
        
        # Trigger upload
        self._handle_upload_request(build_id, local_path)
        
    def _handle_upload_request(self, build_id: str, local_path: str):
        """Handle upload request from view."""
        # Update UI
        self._view.update_build_status(build_id, "uploading")
        
        # Start upload
        self._model.upload_build(build_id, local_path, self._view.platform)
        
    def _handle_build_uploaded(self, build_id: str, blob_url: str):
        """Handle build upload completion."""
        # Update UI
        self._view.update_build_status(build_id, "uploaded")
        self._view.update_upload_status(build_id, f"Uploaded to {blob_url}")
        
    def _handle_upload_retry(self, build_id: str, local_path: str, attempt: int):
        """Handle upload retry notification."""
        # Update UI
        self._view.update_upload_retry(build_id, attempt)
        
    def _handle_install_request(self, build_id: str):
        """Handle install request from preview dialog."""
        build_data = next(
            (build for build in self._model.get_builds() if build["id"] == build_id),
            None
        )
        if not build_data:
            self._view.show_error("Build not found")
            return
            
        local_path = self._model.get_local_path(build_id)
        if not local_path or not os.path.exists(local_path):
            self._view.show_error("Build file not found locally")
            return
            
        try:
            if self._view.platform.lower() == "android":
                self._install_android_build(local_path)
            else:
                self._install_ios_build(local_path)
        except Exception as e:
            logger.error(f"Failed to install build: {e}")
            self._view.show_error(f"Failed to install build: {str(e)}")
            
    def _install_android_build(self, apk_path: str):
        """Install Android build using adb."""
        try:
            # Check if adb is available
            subprocess.run(["adb", "version"], check=True, capture_output=True)
            
            # Get connected devices
            result = subprocess.run(
                ["adb", "devices"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Check if any devices are connected
            devices = [line.split()[0] for line in result.stdout.splitlines()[1:] if line.strip()]
            if not devices:
                raise Exception("No Android devices connected")
                
            # Install on first device
            subprocess.run(
                ["adb", "install", "-r", apk_path],
                check=True,
                capture_output=True
            )
            
            QMessageBox.information(
                self._view,
                "Success",
                "Build installed successfully"
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"ADB command failed: {e.stderr.decode()}")
            
    def _install_ios_build(self, ipa_path: str):
        """Install iOS build using ideviceinstaller."""
        try:
            # Check if ideviceinstaller is available
            subprocess.run(["ideviceinstaller", "-h"], check=True, capture_output=True)
            
            # Get connected devices
            result = subprocess.run(
                ["idevice_id", "-l"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Check if any devices are connected
            devices = result.stdout.strip().splitlines()
            if not devices:
                raise Exception("No iOS devices connected")
                
            # Install on first device
            subprocess.run(
                ["ideviceinstaller", "-i", ipa_path],
                check=True,
                capture_output=True
            )
            
            QMessageBox.information(
                self._view,
                "Success",
                "Build installed successfully"
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"Installation command failed: {e.stderr.decode()}")
            
    def _handle_share_request(self, build_id: str):
        """Handle share request from preview dialog."""
        build_data = next(
            (build for build in self._model.get_builds() if build["id"] == build_id),
            None
        )
        if not build_data:
            self._view.show_error("Build not found")
            return
            
        blob_url = self._model.get_blob_url(build_id)
        if not blob_url:
            self._view.show_error("Build not uploaded yet")
            return
            
        # Copy URL to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(blob_url)
        
        QMessageBox.information(
            self._view,
            "Success",
            "Build URL copied to clipboard"
        )
        
    def cleanup(self):
        """Clean up resources."""
        logger.info(f"Build controller cleaned up for {self._view.platform}") 

    def _show_progress_dialog(self, title: str) -> ProgressDialog:
        """Show progress dialog and return it."""
        if self._progress_dialog:
            self._progress_dialog.close()
        self._progress_dialog = ProgressDialog(title, self.parent())
        self._progress_dialog.cancelled.connect(self._handle_cancel)
        self._progress_dialog.show()
        return self._progress_dialog
        
    def _handle_cancel(self):
        """Handle operation cancellation."""
        try:
            # TODO: Implement actual cancellation logic
            logger.info("Operation cancelled by user")
        except Exception as e:
            logger.error(f"Error handling cancellation: {e}")
            
    @Slot(str)
    def download_build(self, build_id: str, platform: str):
        """Download a build."""
        try:
            self._show_progress("Downloading Build", f"Downloading build {build_id}...")
            
            def progress_callback(progress: int, status: str) -> None:
                if self._progress_dialog:
                    self._progress_dialog.set_progress(progress, status)
                    
            local_path = self._model.download_build(
                build_id=build_id,
                platform=platform,
                progress_callback=progress_callback
            )
            
            self._hide_progress()
            QMessageBox.information(
                None,
                "Download Complete",
                f"Build downloaded successfully to:\n{local_path}"
            )
            
        except AzureServiceError as e:
            self._show_error("Azure Error", str(e))
        except Exception as e:
            self._show_error("Error", f"Failed to download build: {str(e)}")
        finally:
            self._hide_progress()
            
    @Slot(str, str, str)
    def upload_build(self, build_id: str, local_path: str, platform: str):
        """Upload a build."""
        try:
            self._show_progress("Uploading Build", f"Uploading build {build_id}...")
            
            def progress_callback(progress: int, status: str) -> None:
                if self._progress_dialog:
                    self._progress_dialog.set_progress(progress, status)
                    
            blob_url = self._model.upload_build(
                build_id=build_id,
                local_path=local_path,
                platform=platform,
                progress_callback=progress_callback
            )
            
            self._hide_progress()
            QMessageBox.information(
                None,
                "Upload Complete",
                f"Build uploaded successfully to:\n{blob_url}"
            )
            
        except AzureServiceError as e:
            self._show_error("Azure Error", str(e))
        except Exception as e:
            self._show_error("Error", f"Failed to upload build: {str(e)}")
        finally:
            self._hide_progress()
            
    @Slot(str, bool)
    def fetch_builds(self, platform: str, force_refresh: bool = False):
        """Fetch builds for a platform."""
        try:
            self._show_progress("Fetching Builds", "Fetching builds from Azure...")
            
            def progress_callback(progress: int, status: str) -> None:
                if self._progress_dialog:
                    self._progress_dialog.set_progress(progress, status)
                    
            builds = self._model.fetch_builds(
                platform=platform,
                force_refresh=force_refresh,
                progress_callback=progress_callback
            )
            
            self.builds_fetched.emit(builds)
            self._hide_progress()
            
        except AzureServiceError as e:
            self._show_error("Azure Error", str(e))
        except Exception as e:
            self._show_error("Error", f"Failed to fetch builds: {str(e)}")
        finally:
            self._hide_progress()
            
    @Slot(str, dict)
    def filter_builds(self, platform: str, filters: dict):
        """Filter builds based on criteria."""
        try:
            builds = self._model.filter_builds(platform, filters)
            self.builds_fetched.emit(builds)
        except Exception as e:
            logger.error(f"Error filtering builds: {e}")
            self.error_occurred.emit(str(e))
            
    def _show_progress(self, title: str, message: str) -> None:
        """Show progress dialog."""
        self._progress_dialog = ProgressDialog(title, message)
        self._progress_dialog.show()
        
    def _hide_progress(self) -> None:
        """Hide progress dialog."""
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None
            
    def _show_error(self, title: str, message: str) -> None:
        """Show error message."""
        logger.error(f"{title}: {message}")
        self.error_occurred.emit(message)
        QMessageBox.critical(None, title, message) 