"""
Log controller for QuantumOps.
"""
import logging
from typing import Optional
from PySide6.QtCore import QObject, Slot, Signal
from models.log_stream import LogStreamModel
from azure_webapp import AzureWebApp
from datetime import datetime
from PySide6.QtWidgets import QTextEdit

logger = logging.getLogger(__name__)

class LogController(QObject):
    """Controller for log operations."""
    
    log_updated = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, log_area: QTextEdit):
        super().__init__()
        self.log_area = log_area
        
    @Slot(str, str)
    def add_log(self, message: str, level: str = "INFO"):
        """Add a new log entry."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}"
            self.log_area.append(log_entry)
            self.log_area.ensureCursorVisible()
            self.log_updated.emit(log_entry)
        except Exception as e:
            self.error_occurred.emit(f"Failed to add log: {e}") 