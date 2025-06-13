"""
Error Log Viewer component for QuantumOps.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton,
    QSizePolicy
)
from PySide6.QtCore import Qt

class ErrorLogViewer(QWidget):
    """A widget to display error logs."""
    
    def __init__(self, parent: QWidget = None):
        """Initialize the ErrorLogViewer."""
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the UI for the error log viewer."""
        layout = QVBoxLayout()
        
        # Log display area
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Clear button
        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)
        
        layout.addWidget(self.log_display)
        layout.addWidget(self.clear_button)
        
        self.setLayout(layout)
        
    def add_log_message(self, message: str) -> None:
        """Add a message to the log display."""
        self.log_display.append(message)
        
    def clear_logs(self) -> None:
        """Clear all messages from the log display."""
        self.log_display.clear() 