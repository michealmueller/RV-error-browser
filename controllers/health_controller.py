"""
Health check controller for QuantumOps.
"""
import logging
from typing import Optional
from PySide6.QtCore import QObject, Slot, Signal
from PySide6.QtWidgets import QTableWidget
from models.health_check import HealthCheckModel

logger = logging.getLogger(__name__)

class HealthController(QObject):
    """Controller for managing health check operations."""
    
    # Signals
    status_updated = Signal(str, bool)  # webapp, is_healthy
    error_occurred = Signal(str)
    
    def __init__(self, webapps: list, parent):
        super().__init__(parent)
        self._webapps = webapps
        self.model = HealthCheckModel(self._webapps)
        
        # Connect model signals to controller's signals
        self.model.status_updated.connect(self.status_updated)
        self.model.error_occurred.connect(self.error_occurred)
        
    def start_monitoring(self) -> None:
        """Start health check monitoring."""
        logger.info("Starting health check monitoring")
        self.model.start_monitoring()
        
    def stop_monitoring(self) -> None:
        """Stop health check monitoring."""
        logger.info("Stopping health check monitoring")
        self.model.stop_monitoring()
        
    def set_interval(self, interval_ms: int) -> None:
        """Set the health check interval in milliseconds."""
        logger.info(f"Setting health check interval to {interval_ms}ms")
        self.model.set_interval(interval_ms)
        
    def get_health_status(self, webapp: str) -> Optional[bool]:
        """Get the health status for a specific web app."""
        return self.model.get_health_status(webapp)
        
    def get_last_check(self, webapp: str) -> Optional[str]:
        """Get the last check time for a specific web app."""
        last_check = self.model.get_last_check(webapp)
        if last_check:
            return last_check.strftime("%H:%M:%S")
        return None
        
    def cleanup(self) -> None:
        """Clean up resources when the controller is being destroyed."""
        logger.info("Cleaning up health controller")
        self.stop_monitoring()

    def show_settings_dialog(self):
        """Show the health check settings dialog."""
        dialog = HealthSettingsDialog(self.model, self.parent())
        dialog.exec() 