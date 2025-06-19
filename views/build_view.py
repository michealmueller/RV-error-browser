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
    fetch_requested = Signal()
    download_requested = Signal(str, str)  # build_id, platform
    upload_requested = Signal(str, str)  # build_id, local_path
    install_requested = Signal(str)  # build_id
    share_requested = Signal(str)  # build_id
    
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
        refresh_btn.clicked.connect(self.fetch_requested)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Builds table
        self.builds_table = QTableWidget()
        self.builds_table.setColumnCount(6)
        self.builds_table.setHorizontalHeaderLabels([
            "Build ID", "Version", "Status", "Size", "Date", "Actions"
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
                
                # Add action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                # Download button
                download_btn = QPushButton("Download")
                download_btn.clicked.connect(lambda checked, bid=build.get("id", ""): 
                    self.download_requested.emit(bid, self.platform))
                actions_layout.addWidget(download_btn)
                
                # Upload button (only show if downloaded)
                if build.get("status") == "downloaded":
                    upload_btn = QPushButton("Upload")
                    upload_btn.clicked.connect(lambda checked, bid=build.get("id", ""): 
                        self._handle_upload_click(bid))
                    actions_layout.addWidget(upload_btn)
                
                # Install button (only show if downloaded)
                if build.get("status") == "downloaded":
                    install_btn = QPushButton("Install")
                    install_btn.clicked.connect(lambda checked, bid=build.get("id", ""): 
                        self.install_requested.emit(bid))
                    actions_layout.addWidget(install_btn)
                
                # Share button (only show if uploaded)
                if build.get("status") == "uploaded":
                    share_btn = QPushButton("Share")
                    share_btn.clicked.connect(lambda checked, bid=build.get("id", ""): 
                        self.share_requested.emit(bid))
                    actions_layout.addWidget(share_btn)
                
                self.builds_table.setCellWidget(row, 5, actions_widget)
                
            self.status_bar.setText(f"Showing {len(builds)} builds")
            
        except Exception as e:
            logger.error(f"Error updating builds: {e}")
            self._show_error("Update Error", str(e))
    
    def _handle_upload_click(self, build_id: str):
        """Handle upload button click - this would need to get the local path from the model."""
        # For now, emit with empty local_path - the controller should handle this
        self.upload_requested.emit(build_id, "")
            
    def show_error(self, message: str):
        """Show error message in status bar."""
        self.status_bar.setText(f"Error: {message}")
        self.status_bar.setStyleSheet("color: red;")
        
    def clear_error(self):
        """Clear error message from status bar."""
        self.status_bar.clear()
        self.status_bar.setStyleSheet("")
    
    def update_build_status(self, build_id: str, status: str):
        """Update the status of a specific build in the table."""
        try:
            for row in range(self.builds_table.rowCount()):
                if self.builds_table.item(row, 0).text() == build_id:
                    self.builds_table.setItem(row, 2, QTableWidgetItem(status))
                    break
        except Exception as e:
            logger.error(f"Error updating build status: {e}")
    
    def update_upload_status(self, build_id: str, status: str):
        """Update upload status for a build."""
        try:
            for row in range(self.builds_table.rowCount()):
                if self.builds_table.item(row, 0).text() == build_id:
                    # Update status column with upload info
                    current_status = self.builds_table.item(row, 2).text()
                    self.builds_table.setItem(row, 2, QTableWidgetItem(f"{current_status} - {status}"))
                    break
        except Exception as e:
            logger.error(f"Error updating upload status: {e}")
    
    def update_upload_retry(self, build_id: str, attempt: int):
        """Update upload retry information."""
        try:
            for row in range(self.builds_table.rowCount()):
                if self.builds_table.item(row, 0).text() == build_id:
                    current_status = self.builds_table.item(row, 2).text()
                    self.builds_table.setItem(row, 2, QTableWidgetItem(f"{current_status} - Retry {attempt}"))
                    break
        except Exception as e:
            logger.error(f"Error updating upload retry: {e}") 