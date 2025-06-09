"""
Build controller for coordinating between model and view.
"""
import logging
import subprocess
import os
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import QMessageBox
from quantumops.models.build_manager import BuildManager
from quantumops.views.build_view import BuildView
from quantumops.views.progress_dialog import ProgressDialog
from quantumops.services.azure_service import AzureServiceError

logger = logging.getLogger(__name__)

class BuildController(QObject):
    """Controller for managing mobile builds."""
    
    # Signals
    builds_fetched = Signal(list)  # List of build metadata
    build_downloaded = Signal(str, str)  # build_id, local_path
    build_uploaded = Signal(str, str)  # build_id, blob_url
    error_occurred = Signal(str)  # Error message
    upload_retry = Signal(str)  # build_id
    
    # Progress signals
    download_started = Signal(str)  # build_id
    download_progress = Signal(str, int)  # build_id, progress
    upload_started = Signal(str)  # build_id
    upload_progress = Signal(str, int)  # build_id, progress
    
    def __init__(self, model, view):
        """Initialize build controller."""
        super().__init__()
        self.model = model
        self.view = view
        self._progress_dialog = None
        
        # Connect signals
        self.view.download_requested.connect(self._handle_download_request)
        self.view.upload_requested.connect(self._handle_upload_request)
        self.view.install_requested.connect(self._handle_install_request)
        
        logger.info(f"Build controller initialized for {view.platform}")
        
    def _handle_download_request(self, build_id: str):
        """Handle download request from view."""
        try:
            build_data = next(
                (build for build in self.model.get_builds() if build["id"] == build_id),
                None
            )
            if not build_data:
                self.view.show_error("Build not found")
                return
                
            # Show progress dialog
            progress = self._show_progress_dialog("Downloading Build")
            
            def progress_callback(progress_value: int, status: str) -> None:
                if progress:
                    progress.set_progress(progress_value, status)
                    
            try:
                local_path = self.model.download_build(
                    build_id=build_id,
                    platform=self.view.platform,
                    progress_callback=progress_callback
                )
                self.build_downloaded.emit(build_id, local_path)
            except AzureServiceError as e:
                self.view.show_error(f"Azure error: {str(e)}")
            except Exception as e:
                self.view.show_error(f"Download failed: {str(e)}")
            finally:
                if progress:
                    progress.close()
                    
        except Exception as e:
            logger.error(f"Error handling download request: {e}")
            self.view.show_error(f"Error handling download request: {str(e)}")
            
    def _handle_upload_request(self, build_id: str, local_path: str):
        """Handle upload request from view."""
        try:
            if not os.path.exists(local_path):
                self.view.show_error("Build file not found locally")
                return
                
            # Show progress dialog
            progress = self._show_progress_dialog("Uploading Build")
            
            def progress_callback(progress_value: int, status: str) -> None:
                if progress:
                    progress.set_progress(progress_value, status)
                    
            try:
                blob_url = self.model.upload_build(
                    build_id=build_id,
                    local_path=local_path,
                    platform=self.view.platform,
                    progress_callback=progress_callback
                )
                self.build_uploaded.emit(build_id, blob_url)
            except AzureServiceError as e:
                self.view.show_error(f"Azure error: {str(e)}")
                self.upload_retry.emit(build_id)
            except Exception as e:
                self.view.show_error(f"Upload failed: {str(e)}")
                self.upload_retry.emit(build_id)
            finally:
                if progress:
                    progress.close()
                    
        except Exception as e:
            logger.error(f"Error handling upload request: {e}")
            self.view.show_error(f"Error handling upload request: {str(e)}")
            
    def _handle_install_request(self, build_id: str):
        """Handle install request from preview dialog."""
        try:
            build_data = next(
                (build for build in self.model.get_builds() if build["id"] == build_id),
                None
            )
            if not build_data:
                self.view.show_error("Build not found")
                return
                
            local_path = self.model.get_local_path(build_id)
            if not local_path or not os.path.exists(local_path):
                self.view.show_error("Build file not found locally")
                return
                
            try:
                if self.view.platform.lower() == "android":
                    self._install_android_build(local_path)
                else:
                    self._install_ios_build(local_path)
            except subprocess.CalledProcessError as e:
                error_msg = f"Installation command failed: {e.stderr.decode() if e.stderr else str(e)}"
                logger.error(error_msg)
                self.view.show_error(error_msg)
            except Exception as e:
                logger.error(f"Failed to install build: {e}")
                self.view.show_error(f"Failed to install build: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error handling install request: {e}")
            self.view.show_error(f"Error handling install request: {str(e)}")
            
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
                self.view,
                "Success",
                "Build installed successfully"
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"ADB command failed: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Android installation error: {e}")
            raise
            
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
            devices = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            if not devices:
                raise Exception("No iOS devices connected")
                
            # Install on first device
            subprocess.run(
                ["ideviceinstaller", "-i", ipa_path],
                check=True,
                capture_output=True
            )
            
            QMessageBox.information(
                self.view,
                "Success",
                "Build installed successfully"
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"Installation command failed: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"iOS installation error: {e}")
            raise
            
    def _handle_share_request(self, build_id: str):
        """Handle share request from preview dialog."""
        build_data = next(
            (build for build in self.model.get_builds() if build["id"] == build_id),
            None
        )
        if not build_data:
            self.view.show_error("Build not found")
            return
            
        blob_url = self.model.get_blob_url(build_id)
        if not blob_url:
            self.view.show_error("Build not uploaded yet")
            return
            
        # Copy URL to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(blob_url)
        
        QMessageBox.information(
            self.view,
            "Success",
            "Build URL copied to clipboard"
        )
        
    def cleanup(self):
        """Clean up resources."""
        try:
            if self._progress_dialog:
                self._progress_dialog.close()
            logger.info(f"Build controller cleaned up for {self.view.platform}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    def _show_progress_dialog(self, title: str) -> ProgressDialog:
        """Show progress dialog and return it."""
        try:
            if self._progress_dialog:
                self._progress_dialog.close()
            self._progress_dialog = ProgressDialog(title, self.parent())
            self._progress_dialog.cancelled.connect(self._handle_cancel)
            self._progress_dialog.show()
            return self._progress_dialog
        except Exception as e:
            logger.error(f"Error showing progress dialog: {e}")
            return None
            
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
                    
            local_path = self.model.download_build(
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
            
    @Slot(str, bool)
    def fetch_builds(self, platform: str, force_refresh: bool = False):
        """Fetch builds for a platform."""
        try:
            self._show_progress("Fetching Builds", "Fetching builds from Azure...")
            
            def progress_callback(progress: int, status: str) -> None:
                if self._progress_dialog:
                    self._progress_dialog.set_progress(progress, status)
                    
            builds = self.model.fetch_builds(
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
            builds = self.model.filter_builds(platform, filters)
            self.builds_fetched.emit(builds)
        except Exception as e:
            logger.error(f"Error filtering builds: {e}")
            self.error_occurred.emit(str(e))
            
    def _show_progress(self, title: str, message: str) -> None:
        """Show progress dialog."""
        try:
            self._progress_dialog = ProgressDialog(title, message)
            self._progress_dialog.show()
        except Exception as e:
            logger.error(f"Error showing progress: {e}")
            
    def _hide_progress(self) -> None:
        """Hide progress dialog."""
        try:
            if self._progress_dialog:
                self._progress_dialog.close()
                self._progress_dialog = None
        except Exception as e:
            logger.error(f"Error hiding progress: {e}")
            
    def _show_error(self, title: str, message: str) -> None:
        """Show error message."""
        try:
            logger.error(f"{title}: {message}")
            self.error_occurred.emit(message)
            QMessageBox.critical(None, title, message)
        except Exception as e:
            logger.error(f"Error showing error message: {e}") 