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
from PySide6.QtGui import QColor
from datetime import datetime

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
        self.refresh_btn = QPushButton("⟳ Refresh")
        self.refresh_btn.clicked.connect(self.fetch_requested)
        filter_layout.addWidget(self.refresh_btn)
        
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
        
        # Apply styling
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #212529;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #212529;
                margin-right: 4px;
            }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e9ecef;
                color: #212529;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #212529;
                padding: 8px;
                border: none;
                border-right: 1px solid #dee2e6;
                border-bottom: 1px solid #dee2e6;
            }
            QLabel {
                color: #6c757d;
            }
        """)
        
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
            for build in builds:
                row = self.builds_table.rowCount()
                self.builds_table.insertRow(row)
                
                # Build ID
                self.builds_table.setItem(row, 0, QTableWidgetItem(str(build.get("id", ""))))
                
                # Version
                self.builds_table.setItem(row, 1, QTableWidgetItem(str(build.get("version", "unknown"))))
                
                # Status
                status = build.get("status", "unknown")
                status_item = QTableWidgetItem(status)
                if status == "available":
                    status_item.setForeground(QColor("#28a745"))  # Bootstrap success color
                elif status == "downloaded":
                    status_item.setForeground(QColor("#007bff"))  # Bootstrap primary color
                elif status == "uploaded":
                    status_item.setForeground(QColor("#17a2b8"))  # Bootstrap info color
                else:
                    status_item.setForeground(QColor("#6c757d"))  # Bootstrap secondary color
                self.builds_table.setItem(row, 2, status_item)
                
                # Size
                size = build.get("size", 0)
                size_str = self._format_size(size)
                self.builds_table.setItem(row, 3, QTableWidgetItem(size_str))
                
                # Date
                date_str = build.get("date", "")
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        formatted_date = date.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        formatted_date = date_str
                else:
                    formatted_date = "unknown"
                self.builds_table.setItem(row, 4, QTableWidgetItem(formatted_date))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                
                # Download button
                if status == "available":
                    download_btn = QPushButton("Download")
                    download_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #28a745;
                            color: white;
                            border: none;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background-color: #218838;
                        }
                    """)
                    download_btn.clicked.connect(
                        lambda checked, bid=build.get("id", ""): 
                        self.download_requested.emit(bid, self.platform)
                    )
                    actions_layout.addWidget(download_btn)
                
                # Upload button (only show if downloaded)
                if status == "downloaded":
                    upload_btn = QPushButton("Upload")
                    upload_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #007bff;
                            color: white;
                            border: none;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background-color: #0056b3;
                        }
                    """)
                    upload_btn.clicked.connect(
                        lambda checked, bid=build.get("id", ""): 
                        self.upload_requested.emit(bid, build.get("local_path", ""))
                    )
                    actions_layout.addWidget(upload_btn)
                
                # Share button (only show if uploaded)
                if status == "uploaded":
                    share_btn = QPushButton("Share")
                    share_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #17a2b8;
                            color: white;
                            border: none;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background-color: #138496;
                        }
                    """)
                    share_btn.clicked.connect(
                        lambda checked, bid=build.get("id", ""): 
                        self.share_requested.emit(bid)
                    )
                    actions_layout.addWidget(share_btn)
                
                actions_layout.addStretch()
                self.builds_table.setCellWidget(row, 5, actions_widget)
            
            # Update version filter
            versions = sorted(set(build.get("version", "unknown") for build in builds))
            current_version = self.version_filter.currentText()
            self.version_filter.clear()
            self.version_filter.addItem("All Versions", "")
            for version in versions:
                self.version_filter.addItem(str(version), version)
            if current_version in versions:
                index = self.version_filter.findText(current_version)
                if index >= 0:
                    self.version_filter.setCurrentIndex(index)
            
            # Resize columns
            self.builds_table.resizeColumnsToContents()
            
            # Update status
            self.status_bar.setText(f"Showing {len(builds)} builds")
            self.status_bar.setStyleSheet("color: #28a745;")  # Bootstrap success color
            
        except Exception as e:
            logger.error(f"Error updating builds: {e}")
            self.status_bar.setText(f"Error updating builds: {e}")
            self.status_bar.setStyleSheet("color: #dc3545;")  # Bootstrap danger color
            
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
    
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
                    self.builds_table.item(row, 2).setText(status)
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
                    self.builds_table.item(row, 2).setText(f"{current_status} - {status}")
                    break
        except Exception as e:
            logger.error(f"Error updating upload status: {e}")
    
    def update_upload_retry(self, build_id: str, attempt: int):
        """Update upload retry information."""
        try:
            for row in range(self.builds_table.rowCount()):
                if self.builds_table.item(row, 0).text() == build_id:
                    current_status = self.builds_table.item(row, 2).text()
                    self.builds_table.item(row, 2).setText(f"{current_status} - Retry {attempt}")
                    break
        except Exception as e:
            logger.error(f"Error updating upload retry: {e}") 