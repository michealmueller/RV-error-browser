"""UI delegates for custom widget rendering."""

from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette

class StatusDelegate(QStyledItemDelegate):
    """Delegate for rendering build status with custom colors."""
    
    def initStyleOption(self, option, index):
        """Initialize style options with custom colors."""
        super().initStyleOption(option, index)
        
        status = index.data()
        if status == "available":
            option.palette.setColor(QPalette.Text, QColor("#4CAF50"))  # Green
        elif status == "downloaded":
            option.palette.setColor(QPalette.Text, QColor("#2196F3"))  # Blue
        elif status == "installed":
            option.palette.setColor(QPalette.Text, QColor("#9C27B0"))  # Purple
        elif status == "error":
            option.palette.setColor(QPalette.Text, QColor("#F44336"))  # Red

class VersionDelegate(QStyledItemDelegate):
    """Delegate for rendering version numbers."""
    
    def initStyleOption(self, option, index):
        """Initialize style options for version display."""
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter

class DateDelegate(QStyledItemDelegate):
    """Delegate for rendering dates."""
    
    def initStyleOption(self, option, index):
        """Initialize style options for date display."""
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignRight | Qt.AlignVCenter 

"""Dialogs and modal helpers for the QuantumOps UI."""

class DialogPlaceholder:
    pass 