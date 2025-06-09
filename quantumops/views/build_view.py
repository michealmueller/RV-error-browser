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
    download_requested = Signal(str)  # build_id
    upload_requested = Signal(str, str)  # build_id, local_path
    install_requested = Signal(str)  # build_id
    filter_changed = Signal(dict)  # filter criteria
    build_selected = Signal(str)  # build_id
    refresh_requested = Signal()
    
    def __init__(self, platform: str, parent: Optional[QWidget] = None):
        """Initialize build view."""
        super().__init__(parent)
        self.platform = platform
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the user interface."""
        try:
            # Main layout
            layout = QVBoxLayout(self)
            
            # Search and filter bar
            filter_layout = QHBoxLayout()
            
            # Search input
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search builds...")
            filter_layout.addWidget(self.search_input)
            
            # Version filter
            self.version_filter = QComboBox()
            self.version_filter.addItem("All Versions", "")
            filter_layout.addWidget(self.version_filter)
            
            # Status filter
            self.status_filter = QComboBox()
            self.status_filter.addItem("All Statuses", "")
            self.status_filter.addItem("Available", "available")
            self.status_filter.addItem("Downloaded", "downloaded")
            self.status_filter.addItem("Uploaded", "uploaded")
            filter_layout.addWidget(self.status_filter)
            
            layout.addLayout(filter_layout)
            
            # Builds table
            self.builds_table = QTableWidget()
            self.builds_table.setColumnCount(5)
            self.builds_table.setHorizontalHeaderLabels([
                "ID", "Version", "Status", "Size", "Date"
            ])
            self.builds_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.builds_table.setSelectionMode(QTableWidget.SingleSelection)
            layout.addWidget(self.builds_table)
            
            # Status bar
            self.status_bar = QLabel()
            layout.addWidget(self.status_bar)
            
        except Exception as e:
            logger.error(f"Error setting up UI: {e}")
            self._show_error("UI Setup Error", str(e))
            
    def _connect_signals(self):
        """Connect signals to slots."""
        try:
            self.search_input.textChanged.connect(self._handle_search)
            self.version_filter.currentIndexChanged.connect(self._handle_filter_change)
            self.status_filter.currentIndexChanged.connect(self._handle_filter_change)
            self.builds_table.itemSelectionChanged.connect(self._handle_selection)
        except Exception as e:
            logger.error(f"Error connecting signals: {e}")
            self._show_error("Signal Connection Error", str(e))
            
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
                
                # Get the local path for the selected build
                local_path = self.get_local_path(build_id)
                if local_path:
                    self.upload_requested.emit(build_id, local_path)
        except Exception as e:
            logger.error(f"Error handling selection: {e}")
            self._show_error("Selection Error", str(e))
            
    def get_local_path(self, build_id: str) -> Optional[str]:
        """Get the local path for a build."""
        try:
            # This should be implemented to return the actual local path
            # For now, we'll return a placeholder
            return f"/tmp/builds/{build_id}"
        except Exception as e:
            logger.error(f"Error getting local path: {e}")
            return None
            
    def _show_error(self, title: str, message: str):
        """Show error message to user."""
        try:
            QMessageBox.critical(self, title, message)
        except Exception as e:
            logger.error(f"Error showing error message: {e}")
            
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
                try:
                    self.builds_table.setItem(row, 0, QTableWidgetItem(build.get("id", "")))
                    self.builds_table.setItem(row, 1, QTableWidgetItem(build.get("version", "")))
                    self.builds_table.setItem(row, 2, QTableWidgetItem(build.get("status", "")))
                    self.builds_table.setItem(row, 3, QTableWidgetItem(str(build.get("size", 0))))
                    self.builds_table.setItem(row, 4, QTableWidgetItem(build.get("date", "")))
                except Exception as e:
                    logger.error(f"Error populating row {row}: {e}")
                    continue
                    
            self.status_bar.setText(f"Showing {len(builds)} builds")
            
        except Exception as e:
            logger.error(f"Error updating builds: {e}")
            self._show_error("Update Error", str(e))
            
    def update_build_status(self, build_id: str, status: str):
        """Update the status of a build in the table."""
        try:
            for row in range(self.builds_table.rowCount()):
                if self.builds_table.item(row, 0).text() == build_id:
                    self.builds_table.setItem(row, 2, QTableWidgetItem(status))
                    break
        except Exception as e:
            logger.error(f"Error updating build status: {e}")
            
    def update_upload_status(self, build_id: str, status: str):
        """Update the upload status of a build in the table."""
        try:
            for row in range(self.builds_table.rowCount()):
                if self.builds_table.item(row, 0).text() == build_id:
                    current_status = self.builds_table.item(row, 2).text()
                    self.builds_table.setItem(row, 2, QTableWidgetItem(f"{current_status} - {status}"))
                    break
        except Exception as e:
            logger.error(f"Error updating upload status: {e}")
            
    def update_upload_retry(self, build_id: str, attempt: int):
        """Update the upload retry status of a build in the table."""
        try:
            for row in range(self.builds_table.rowCount()):
                if self.builds_table.item(row, 0).text() == build_id:
                    current_status = self.builds_table.item(row, 2).text()
                    self.builds_table.setItem(row, 2, QTableWidgetItem(f"{current_status} (Retry {attempt})"))
                    break
        except Exception as e:
            logger.error(f"Error updating upload retry status: {e}")
            
    def show_error(self, message: str):
        """Show error message."""
        try:
            self._show_error("Error", message)
        except Exception as e:
            logger.error(f"Error showing error message: {e}")
            
    def cleanup(self):
        """Clean up resources."""
        try:
            # Clear table
            self.builds_table.setRowCount(0)
            # Clear filters
            self.search_input.clear()
            self.version_filter.setCurrentIndex(0)
            self.status_filter.setCurrentIndex(0)
            # Clear status
            self.status_bar.clear()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 