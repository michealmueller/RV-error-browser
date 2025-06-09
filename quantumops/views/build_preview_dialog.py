"""
Dialog for previewing build artifacts and their metadata.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

class BuildPreviewDialog(QDialog):
    """Dialog for previewing build artifacts."""
    
    # Signals
    install_requested = Signal(str)  # build_id
    share_requested = Signal(str)  # build_id
    
    def __init__(self, build_data: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.build_data = build_data
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Build Preview")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Header with build ID and status
        header_layout = QHBoxLayout()
        build_id_label = QLabel(f"Build ID: {self.build_data.get('id', '')}")
        build_id_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(build_id_label)
        
        status = self.build_data.get("status", "").lower()
        status_label = QLabel(status.title())
        status_label.setStyleSheet(
            f"color: {self._get_status_color(status)}; "
            "font-size: 14px; font-weight: bold;"
        )
        header_layout.addWidget(status_label)
        header_layout.addStretch()
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        install_btn = QPushButton("Install")
        install_btn.clicked.connect(
            lambda: self.install_requested.emit(self.build_data["id"])
        )
        install_btn.setEnabled(status == "finished")
        actions_layout.addWidget(install_btn)
        
        share_btn = QPushButton("Share")
        share_btn.clicked.connect(
            lambda: self.share_requested.emit(self.build_data["id"])
        )
        share_btn.setEnabled(status == "finished")
        actions_layout.addWidget(share_btn)
        
        # Metadata table
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.metadata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.metadata_table.setAlternatingRowColors(True)
        
        # Add metadata rows
        self._add_metadata_row("Version", self.build_data.get("appVersion", ""))
        self._add_metadata_row("Created", self._format_date(self.build_data.get("createdAt")))
        self._add_metadata_row("Platform", self.build_data.get("platform", "").title())
        self._add_metadata_row("Build Number", str(self.build_data.get("buildNumber", "")))
        self._add_metadata_row("Branch", self.build_data.get("sourceBranch", ""))
        self._add_metadata_row("Commit", self.build_data.get("sourceVersion", ""))
        
        # Add widgets to layout
        layout.addLayout(header_layout)
        layout.addLayout(actions_layout)
        layout.addWidget(self.metadata_table)
        
    def _add_metadata_row(self, property_name: str, value: str):
        """Add a row to the metadata table."""
        row = self.metadata_table.rowCount()
        self.metadata_table.insertRow(row)
        
        property_item = QTableWidgetItem(property_name)
        property_item.setFlags(property_item.flags() & ~Qt.ItemIsEditable)
        self.metadata_table.setItem(row, 0, property_item)
        
        value_item = QTableWidgetItem(value)
        value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
        self.metadata_table.setItem(row, 1, value_item)
        
    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        if not date_str:
            return ""
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return date_str
            
    def _get_status_color(self, status: str) -> str:
        """Get color for build status."""
        colors = {
            "finished": "#2ecc71",  # Green
            "in_progress": "#f1c40f",  # Yellow
            "error": "#e74c3c",  # Red
            "canceled": "#95a5a6",  # Gray
            "downloaded": "#3498db",  # Blue
            "uploading": "#9b59b6",  # Purple
            "uploaded": "#2ecc71",  # Green
        }
        return colors.get(status, "#000000")  # Default to black 