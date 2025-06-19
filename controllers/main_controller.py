"""
Main controller for the application.
"""
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from models.build_manager import BuildManager
from views.main_window import MainWindow

logger = logging.getLogger(__name__)

class MainController(QObject):
    """Main controller for the application."""
    
    # Signals
    build_list_updated = Signal(list)
    build_status_changed = Signal(str, str)  # build_id, status
    error_occurred = Signal(str)
    
    def __init__(self, model: BuildManager, view: MainWindow):
        """Initialize main controller."""
        super().__init__()
        self.model = model
        self.view = view
        
        # Connect signals
        self.view.refresh_builds.connect(self.refresh_builds)
        self.view.download_selected.connect(self.download_builds)
        self.view.upload_selected.connect(self.upload_builds)
        
        # Connect model signals
        self.model.build_list_updated.connect(self.build_list_updated)
        self.model.build_status_changed.connect(self.build_status_changed)
        self.model.error_occurred.connect(self.error_occurred)
        
        # Initial refresh
        self.refresh_builds()
        
    @Slot()
    def refresh_builds(self):
        """Refresh build list."""
        try:
            platform = self.view.platform_combo.currentText()
            self.model.refresh_builds(platform)
        except Exception as e:
            logger.error(f"Failed to refresh builds: {e}")
            self.error_occurred.emit(str(e))
            
    @Slot(list)
    def download_builds(self, build_ids: list):
        """Download selected builds."""
        try:
            platform = self.view.platform_combo.currentText()
            for build_id in build_ids:
                self.model.download_build(build_id, platform)
        except Exception as e:
            logger.error(f"Failed to download builds: {e}")
            self.error_occurred.emit(str(e))
            
    @Slot(list)
    def upload_builds(self, build_ids: list):
        """Upload selected builds."""
        try:
            platform = self.view.platform_combo.currentText()
            for build_id in build_ids:
                self.model.upload_build(build_id, platform)
        except Exception as e:
            logger.error(f"Failed to upload builds: {e}")
            self.error_occurred.emit(str(e))
            
    @Slot(str, str)
    def install_build(self, build_id: str, device_id: Optional[str] = None):
        """Install build on device."""
        try:
            platform = self.view.platform_combo.currentText()
            self.model.install_build(build_id, platform, device_id)
        except Exception as e:
            logger.error(f"Failed to install build: {e}")
            self.error_occurred.emit(str(e))
            
    @Slot(str)
    def share_build(self, build_id: str):
        """Share build URL."""
        try:
            platform = self.view.platform_combo.currentText()
            self.model.share_build(build_id, platform)
        except Exception as e:
            logger.error(f"Failed to share build: {e}")
            self.error_occurred.emit(str(e)) 