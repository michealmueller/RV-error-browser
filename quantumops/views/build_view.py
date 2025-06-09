"""
Build view for displaying and managing mobile builds.
"""
import logging
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, Slot

logger = logging.getLogger(__name__)

class BuildView(QWidget):
    """View for displaying and managing mobile builds."""
    
    # Signals
    build_selected = Signal(str)  # build_id
    filter_changed = Signal(dict)  # filter criteria
    refresh_requested = Signal()
    
    def __init__(self, platform: str):
        super().__init__()
        self.platform = platform
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search builds...")
        self.search_input.textChanged.connect(self._handle_search)
        filter_layout.addWidget(self.search_input)
        
        # Version filter
        self.version_filter = QComboBox()
        self.version_filter.addItem("All Versions", "")
        self.version_filter.currentIndexChanged.connect(self._handle_filter_change)
        filter_layout.addWidget(self.version_filter)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", "")
        self.status_filter.addItem("Available", "available")
        self.status_filter.addItem("Downloaded", "downloaded")
        self.status_filter.addItem("Uploaded", "uploaded")
        self.status_filter.currentIndexChanged.connect(self._handle_filter_change)
        filter_layout.addWidget(self.status_filter)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_requested)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Builds table
        self.builds_table = QTableWidget()
        self.builds_table.setColumnCount(5)
        self.builds_table.setHorizontalHeaderLabels([
            "Build ID", "Version", "Status", "Size", "Date"
        ])
        self.builds_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.builds_table.setSelectionMode(QTableWidget.SingleSelection)
        self.builds_table.itemSelectionChanged.connect(self._handle_selection)
        layout.addWidget(self.builds_table)
        
        # Status bar
        self.status_bar = QLabel()
        layout.addWidget(self.status_bar)
        
    def _handle_search(self, text: str):
        """Handle search input changes."""
        try:
            self.filter_changed.emit({
                "search": text,
                "version": self.version_filter.currentData(),
                "status": self.status_filter.currentData()
            })
        except Exception as e:
            logger.error(f"Error handling search: {e}")
            self._show_error("Search Error", str(e))
            
    def _handle_filter_change(self):
        """Handle filter selection changes."""
        try:
            self.filter_changed.emit({
                "search": self.search_input.text(),
                "version": self.version_filter.currentData(),
                "status": self.status_filter.currentData()
            })
        except Exception as e:
            logger.error(f"Error handling filter change: {e}")
            self._show_error("Filter Error", str(e))
            
    def _handle_selection(self):
        """Handle build selection."""
        try:
            selected = self.builds_table.selectedItems()
            if selected:
                build_id = selected[0].text()
                self.build_selected.emit(build_id)
        except Exception as e:
            logger.error(f"Error handling selection: {e}")
            self._show_error("Selection Error", str(e))
            
    def _show_error(self, title: str, message: str):
        """Show error message to user."""
        QMessageBox.critical(self, title, message)
        
    def update_builds(self, builds: List[Dict]):
        """Update the builds table with new data."""
        try:
            self.builds_table.setRowCount(0)
            if not builds:
                self.status_bar.setText("No builds found")
                return
                
            self.builds_table.setRowCount(len(builds))
            
            # Update version filter
            versions = sorted(set(build.get("version", "") for build in builds))
            current_version = self.version_filter.currentData()
            self.version_filter.clear()
            self.version_filter.addItem("All Versions", "")
            for version in versions:
                if version:  # Skip empty versions
                    self.version_filter.addItem(version, version)
            if current_version:
                index = self.version_filter.findData(current_version)
                if index >= 0:
                    self.version_filter.setCurrentIndex(index)
                    
            # Populate table
            for row, build in enumerate(builds):
                self.builds_table.setItem(row, 0, QTableWidgetItem(build.get("id", "")))
                self.builds_table.setItem(row, 1, QTableWidgetItem(build.get("version", "")))
                self.builds_table.setItem(row, 2, QTableWidgetItem(build.get("status", "")))
                self.builds_table.setItem(row, 3, QTableWidgetItem(str(build.get("size", 0))))
                self.builds_table.setItem(row, 4, QTableWidgetItem(build.get("date", "")))
                
            self.status_bar.setText(f"Showing {len(builds)} builds")
            
        except Exception as e:
            logger.error(f"Error updating builds: {e}")
            self._show_error("Update Error", str(e))
            
    def show_error(self, message: str):
        """Show error message in status bar."""
        self.status_bar.setText(f"Error: {message}")
        self.status_bar.setStyleSheet("color: red;")
        
    def clear_error(self):
        """Clear error message from status bar."""
        self.status_bar.clear()
        self.status_bar.setStyleSheet("") 