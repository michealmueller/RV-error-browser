"""
Log controller for QuantumOps.
"""
import logging
from typing import Optional
from PySide6.QtCore import QObject, Slot, Signal
from quantumops.models.log_stream import LogStreamModel
from quantumops.azure_webapp import AzureWebApp

logger = logging.getLogger(__name__)

class LogController(QObject):
    """Controller for managing log streaming operations."""
    
    log_message = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, azure_webapp: AzureWebApp):
        super().__init__()
        self.model = LogStreamModel(azure_webapp)
        self._setup_connections()
        
    def _setup_connections(self) -> None:
        """Set up signal connections between model and UI."""
        self.model.log_received.connect(self._handle_log_received)
        self.model.error_occurred.connect(self._handle_error)
        self.model.status_changed.connect(self._handle_status_change)
        
    @Slot(str)
    def _handle_log_received(self, line: str) -> None:
        """Handle a received log line."""
        logger.debug(f"Received log line: {line[:100]}...")
        self.log_message.emit(line)
        
    @Slot(str)
    def _handle_error(self, error: str) -> None:
        """Handle an error from the model."""
        logger.error(f"Log streaming error: {error}")
        self.error_occurred.emit(error)
        
    @Slot(str)
    def _handle_status_change(self, status: str) -> None:
        """Handle a status change from the model."""
        logger.info(f"Log streaming status: {status}")
        
    def start_streaming(self, resource_group: str, web_app_name: str) -> None:
        """Start streaming logs from the specified web app."""
        logger.info(f"Starting log stream for {web_app_name} in {resource_group}")
        self.model.start_streaming(resource_group, web_app_name)
        
    def stop_streaming(self) -> None:
        """Stop the log streaming."""
        logger.info("Stopping log stream")
        self.model.stop_streaming()
        
    def get_log_buffer(self) -> list:
        """Get the current log buffer."""
        return self.model.get_log_buffer()
        
    def clear_buffer(self) -> None:
        """Clear the log buffer."""
        self.model.clear_buffer() 