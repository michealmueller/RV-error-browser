"""
Status indicator widget for QuantumOps.
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class StatusIndicator(QLabel):
    """Custom widget for displaying status."""
    
    def __init__(self, parent=None):
        """Initialize status indicator.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.set_status("disconnected")
    
    def set_status(self, status: str):
        """Set the status indicator color.
        
        Args:
            status: Status string ("connected" or "disconnected")
        """
        color = QColor("#2ecc71") if status == "connected" else QColor("#e74c3c")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color.name()};
                border-radius: 6px;
                border: 1px solid #2d2d2d;
            }}
        """) 