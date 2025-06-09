"""
Health check controller for QuantumOps.
"""
import logging
from typing import Optional
from PySide6.QtCore import QObject, Slot, Signal
from quantumops.models.health_check import HealthCheckModel

logger = logging.getLogger(__name__)

class HealthController(QObject):
    """Controller for managing health check operations."""
    
    # Signals
    status_updated = Signal(str, bool)  # webapp, is_healthy
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.model = HealthCheckModel()
        self._setup_connections()
        
    def _setup_connections(self) -> None:
        """Set up signal connections between model and UI."""
        self.model.status_updated.connect(self._handle_status_update)
        self.model.error_occurred.connect(self._handle_error)
        
    @Slot(str, bool)
    def _handle_status_update(self, webapp: str, is_healthy: bool) -> None:
        """Handle a health status update from the model."""
        logger.debug(f"Health status update for {webapp}: {'Healthy' if is_healthy else 'Unhealthy'}")
        self.status_updated.emit(webapp, is_healthy)
        
    @Slot(str)
    def _handle_error(self, error: str) -> None:
        """Handle an error from the model."""
        logger.error(f"Health check error: {error}")
        self.error_occurred.emit(error)
        
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
        """Clean up resources when the application closes."""
        logger.info("Cleaning up health controller")
        self.stop_monitoring() 