"""
Progress dialog for tracking build operations.
"""
import logging
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer

logger = logging.getLogger(__name__)

class ProgressDialog(QDialog):
    """Dialog for showing operation progress."""
    
    # Signals
    cancelled = Signal()
    
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._handle_cancel)
        layout.addWidget(self.cancel_button)
        
    def _handle_cancel(self):
        """Handle cancel button click."""
        try:
            self.cancelled.emit()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Cancelling...")
        except Exception as e:
            logger.error(f"Error handling cancel: {e}")
            
    def update_progress(self, value: int, status: str):
        """Update progress bar and status."""
        try:
            self.progress_bar.setValue(value)
            self.status_label.setText(status)
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            
    def set_indeterminate(self, status: str):
        """Set progress bar to indeterminate mode."""
        try:
            self.progress_bar.setRange(0, 0)
            self.status_label.setText(status)
        except Exception as e:
            logger.error(f"Error setting indeterminate mode: {e}")
            
    def set_determinate(self, status: str):
        """Set progress bar to determinate mode."""
        try:
            self.progress_bar.setRange(0, 100)
            self.status_label.setText(status)
        except Exception as e:
            logger.error(f"Error setting determinate mode: {e}")
            
    def show_error(self, message: str):
        """Show error message and disable cancel button."""
        try:
            self.status_label.setText(f"Error: {message}")
            self.status_label.setStyleSheet("color: red;")
            self.cancel_button.setEnabled(False)
        except Exception as e:
            logger.error(f"Error showing error message: {e}")
            
    def show_success(self, message: str):
        """Show success message and disable cancel button."""
        try:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: green;")
            self.cancel_button.setEnabled(False)
            QTimer.singleShot(2000, self.close)
        except Exception as e:
            logger.error(f"Error showing success message: {e}")
            
    def closeEvent(self, event):
        """Handle dialog close event."""
        try:
            self.cancelled.emit()
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"Error handling close event: {e}")
            event.accept() 