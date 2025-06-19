"""
Main window view for QuantumOps.
"""
import logging
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox,
    QGroupBox, QSplitter, QMenu, QTabWidget, QMessageBox,
    QTableWidget, QTableWidgetItem, QMenuBar, QFileDialog,
    QStatusBar, QProgressBar, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QColor, QPalette, QAction
from controllers.log_controller import LogController
from controllers.health_controller import HealthController
from controllers.database_controller import DatabaseController
from azure_webapp import AzureWebApp
from models.database import DatabaseModel
from views.database_view import DatabaseView
from views.build_view import BuildView
from models.build_manager import BuildManager
from controllers.build_controller import BuildController
from models.history_manager import HistoryManager
from .history_dialog import HistoryDialog
from .preview_dialog import PreviewDialog
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class StatusIndicator(QLabel):
    """Custom widget for displaying health status."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.set_status(False)
        
    def set_status(self, is_healthy: bool) -> None:
        """Set the status indicator color."""
        color = QColor("#28a745") if is_healthy else QColor("#dc3545")  # Bootstrap success/danger colors
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color.name()};
                border-radius: 6px;
                border: 1px solid #dee2e6;
            }}
        """)

class ProgressDialog(QDialog):
    """Dialog for showing operation progress."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
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
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
    def update_progress(self, value: int, status: str):
        """Update progress bar and status."""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
        
    def set_indeterminate(self, status: str):
        """Set progress bar to indeterminate mode."""
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(status)

class MainWindow(QMainWindow):
    """Main window for the application."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.webapps = self._load_webapps()
        self.selected_webapp = self.webapps[0] if self.webapps else None
        self.history_manager = HistoryManager()
        self._init_ui()
        self._setup_controllers()
        self._setup_build_managers()
        self._connect_signals()
        self._setup_status_bar()
        self._progress_dialog = None
        logger.info("Main window initialized")
        
    def _init_ui(self):
        """Initialize the UI components with a simplified, user-friendly design."""
        self.setWindowTitle("QuantumOps - Mobile Build Manager")
        self.setMinimumSize(1400, 900)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create header section
        self._create_header(main_layout)
        
        # Create main content area
        self._create_main_content(main_layout)
        
        # Create status bar
        self._setup_status_bar()
        
        # Create menu bar
        self._create_menu_bar()
        
        # Connect signals
        self._connect_ui_signals()
        
        # Set application-wide stylesheet for light theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                background-color: #ffffff;
                color: #212529;
            }
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #495057;
            }
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
            QTableWidget::item:selected {
                background-color: #e9ecef;
                color: #212529;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                color: #212529;
                border: none;
                padding: 4px;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px;
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
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px 8px;
                color: #212529;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            QStatusBar {
                background-color: #f8f9fa;
                color: #212529;
            }
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #e9ecef;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #e9ecef;
            }
        """)
        
    def _create_header(self, parent_layout):
        """Create the header section with platform selector and main actions."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # App title
        title_label = QLabel("QuantumOps")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Platform selector
        platform_label = QLabel("Platform:")
        platform_label.setStyleSheet("font-weight: bold; color: #34495e;")
        header_layout.addWidget(platform_label)
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Android", "iOS"])
        self.platform_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #34495e;
            }
        """)
        header_layout.addWidget(self.platform_combo)
        
        # Azure Web App selector
        webapp_label = QLabel("Azure Web App:")
        webapp_label.setStyleSheet("font-weight: bold; color: #34495e; margin-left: 20px;")
        header_layout.addWidget(webapp_label)
        
        self.webapp_combo = QComboBox()
        for webapp in self.webapps:
            label = f"{webapp['name']} ({webapp['resource_group']})"
            self.webapp_combo.addItem(label, webapp)
        self.webapp_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #34495e;
            }
        """)
        header_layout.addWidget(self.webapp_combo)
        
        parent_layout.addWidget(header_widget)
        
    def _create_main_content(self, parent_layout):
        """Create the main content area with builds table and controls."""
        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Create controls section
        self._create_controls_section(content_layout)
        
        # Create builds table section
        self._create_builds_section(content_layout)
        
        # Create bottom panels
        self._create_bottom_panels(content_layout)
        
        parent_layout.addWidget(content_widget, 1)  # Give it most of the space
        
    def _create_controls_section(self, parent_layout):
        """Create the controls section with search and filters."""
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold; color: #34495e;")
        controls_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search builds by ID, version, or status...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        controls_layout.addWidget(self.search_input, 1)  # Give it more space
        
        # Version filter
        version_label = QLabel("Version:")
        version_label.setStyleSheet("font-weight: bold; color: #34495e; margin-left: 15px;")
        controls_layout.addWidget(version_label)
        
        self.version_filter = QComboBox()
        self.version_filter.addItem("All Versions", "")
        self.version_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
                min-width: 120px;
            }
        """)
        controls_layout.addWidget(self.version_filter)
        
        # Status filter
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: bold; color: #34495e; margin-left: 15px;")
        controls_layout.addWidget(status_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", "")
        self.status_filter.addItem("Available", "available")
        self.status_filter.addItem("Downloaded", "downloaded")
        self.status_filter.addItem("Uploaded", "uploaded")
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
                min-width: 120px;
            }
        """)
        controls_layout.addWidget(self.status_filter)
        
        # Refresh button
        self.refresh_button = QPushButton("⟳ Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        controls_layout.addWidget(self.refresh_button)
        
        parent_layout.addWidget(controls_widget)
        
    def _create_builds_section(self, parent_layout):
        """Create the builds table section."""
        builds_group = QGroupBox("Builds")
        builds_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        builds_layout = QVBoxLayout(builds_group)
        
        # Create builds table
        self.builds_table = QTableWidget()
        self.builds_table.setColumnCount(7)
        self.builds_table.setHorizontalHeaderLabels([
            "Build ID", "Version", "Status", "Size", "Date", "Actions", "Share"
        ])
        self.builds_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.builds_table.setSelectionMode(QTableWidget.SingleSelection)
        self.builds_table.setAlternatingRowColors(True)
        self.builds_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #dee2e6;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 12px 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Set column widths
        self.builds_table.setColumnWidth(0, 200)  # Build ID
        self.builds_table.setColumnWidth(1, 120)  # Version
        self.builds_table.setColumnWidth(2, 100)  # Status
        self.builds_table.setColumnWidth(3, 80)   # Size
        self.builds_table.setColumnWidth(4, 150)  # Date
        self.builds_table.setColumnWidth(5, 200)  # Actions
        self.builds_table.setColumnWidth(6, 100)  # Share
        
        builds_layout.addWidget(self.builds_table)
        
        parent_layout.addWidget(builds_group, 1)  # Give it most of the space
        
    def _create_bottom_panels(self, parent_layout):
        """Create the bottom panels for health status and logs."""
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setSpacing(15)
        
        # Health status panel
        health_group = QGroupBox("System Health")
        health_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        health_layout = QVBoxLayout(health_group)
        
        self.health_status = QLabel("Checking system health...")
        self.health_status.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        health_layout.addWidget(self.health_status)
        
        bottom_layout.addWidget(health_group)
        
        # Log panel
        log_group = QGroupBox("System Log")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        log_layout.addWidget(self.log_area)
        
        bottom_layout.addWidget(log_group, 1)  # Give logs more space
        
        parent_layout.addWidget(bottom_widget)
        
    def _connect_ui_signals(self):
        """Connect UI signals to their handlers."""
        # Platform and webapp changes
        self.platform_combo.currentTextChanged.connect(self._on_platform_changed)
        self.webapp_combo.currentIndexChanged.connect(self._on_webapp_changed)
        
        # Search and filters
        self.search_input.textChanged.connect(self._on_search_changed)
        self.version_filter.currentIndexChanged.connect(self._on_filter_changed)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        
        # Refresh button
        self.refresh_button.clicked.connect(self.refresh_builds)
        
    def _on_search_changed(self, text: str):
        """Handle search input changes."""
        logger.debug(f"Search text changed: {text}")
        # TODO: Implement search functionality
        
    def _on_filter_changed(self):
        """Handle filter changes."""
        logger.debug("Filters changed")
        # TODO: Implement filter functionality
        
    def _setup_controllers(self):
        """Set up controllers."""
        # Health controller
        self.health_controller = HealthController()
        self.health_controller.status_updated.connect(self._update_health_status)
        
        # Log controller
        self.log_controller = LogController(self.selected_webapp)
        self.log_controller.log_message.connect(self._append_log)
        
        # Database controller (for error browser functionality)
        self.database_model = DatabaseModel()
        self.database_view = DatabaseView()
        self.database_controller = DatabaseController(self.database_model, self.database_view)
        
    def _setup_build_managers(self):
        """Set up build managers and controllers."""
        # Create models
        self.android_model = BuildManager()
        self.ios_model = BuildManager()
        
        # Create build views for each platform
        self.android_view = BuildView("android")
        self.ios_view = BuildView("ios")
        
        # Create controllers
        self.android_controller = BuildController(self.android_model, self.android_view)
        self.ios_controller = BuildController(self.ios_model, self.ios_view)
        
        # Connect upload signals
        self.android_view.upload_requested.connect(self._handle_android_upload)
        self.ios_view.upload_requested.connect(self._handle_ios_upload)
        
    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        refresh_action = file_menu.addAction("Refresh")
        refresh_action.triggered.connect(self.refresh_builds)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        history_action = view_menu.addAction("Build History")
        history_action.triggered.connect(self.show_history)
        
        error_browser_action = view_menu.addAction("Error Browser")
        error_browser_action.triggered.connect(self.show_error_browser)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        sp_info_action = QAction("View SP Info", self)
        sp_info_action.triggered.connect(self._show_sp_info)
        settings_menu.addAction(sp_info_action)
        
    def _update_health_status(self, status: dict):
        """Update health status display."""
        text = []
        for app, health in status.items():
            color = "green" if health["healthy"] else "red"
            text.append(f'<span style="color: {color}">●</span> {app}: {health["message"]}')
        self.health_status.setText("<br>".join(text))
        
    def _append_log(self, message: str):
        """Append message to log area."""
        self.log_area.append(message)
        
    def _set_health_interval(self, interval: int):
        """Set health check interval."""
        self.health_controller.set_interval(interval)
        
    def _show_sp_info(self):
        """Show service principal info dialog."""
        # TODO: Implement SP info dialog
        pass
        
    def show_error_browser(self):
        """Show the error browser dialog."""
        self.database_view.show()
        
    def _handle_android_upload(self, build_id: str, local_path: str):
        """Handle Android build upload request."""
        try:
            self.android_controller.upload_build(build_id, local_path, "android")
        except Exception as e:
            self._handle_error(f"Failed to upload Android build: {e}")
        
    def _handle_ios_upload(self, build_id: str, local_path: str):
        """Handle iOS build upload request."""
        try:
            self.ios_controller.upload_build(build_id, local_path, "ios")
        except Exception as e:
            self._handle_error(f"Failed to upload iOS build: {e}")
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up controllers
        self.database_controller.cleanup()
        self.health_controller.cleanup()
        self.android_controller.cleanup()
        self.ios_controller.cleanup()
        event.accept()
        
    def show_history(self):
        """Show history dialog."""
        dialog = HistoryDialog(self.history_manager, self)
        dialog.exec()
        
    def refresh_builds(self):
        """Refresh build list for the current platform."""
        try:
            platform = self.platform_combo.currentText().lower()
            if platform == "android":
                self.android_model.fetch_builds("android", force_refresh=True)
            elif platform == "ios":
                self.ios_model.fetch_builds("ios", force_refresh=True)
        except Exception as e:
            self._handle_error(f"Failed to refresh builds: {e}")
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About QuantumOps",
            "QuantumOps - Mobile Build Manager\n\n"
            "Version 1.0.0\n"
            "© 2024 Rosie Vision"
        )
        
    def _load_webapps(self):
        config_path = Path("config/webapps.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return []
        
    def _on_webapp_changed(self, idx):
        self.selected_webapp = self.webapp_combo.currentData()
        # Re-instantiate LogController with new webapp
        self.log_controller = LogController(self.selected_webapp)
        # ... any additional logic to update log view ... 

    def _on_platform_changed(self, platform: str):
        """Handle platform selection change."""
        logger.info(f"Platform changed to: {platform}")
        # Update the builds table based on the selected platform
        self._update_builds_table(platform.lower())
        
    def _update_builds_table(self, platform: str):
        """Update the builds table with data for the selected platform."""
        try:
            if platform == "android":
                builds = self.android_model.get_builds()
            elif platform == "ios":
                builds = self.ios_model.get_builds()
            else:
                builds = []
                
            self._populate_builds_table(builds)
        except Exception as e:
            logger.error(f"Error updating builds table: {e}")
            self._handle_error(f"Failed to update builds table: {e}")
            
    def _populate_builds_table(self, builds: list):
        """Populate the builds table with the given builds data."""
        self.builds_table.setRowCount(0)
        if not builds:
            return
            
        self.builds_table.setRowCount(len(builds))
        
        for row, build in enumerate(builds):
            # Build ID
            self.builds_table.setItem(row, 0, QTableWidgetItem(build.get("id", "")))
            
            # Version
            self.builds_table.setItem(row, 1, QTableWidgetItem(build.get("version", "")))
            
            # Status with color coding
            status_item = QTableWidgetItem(build.get("status", ""))
            status = build.get("status", "")
            if status == "uploaded":
                status_item.setBackground(QColor("#d4edda"))  # Light green
            elif status == "downloaded":
                status_item.setBackground(QColor("#d1ecf1"))  # Light blue
            elif status == "available":
                status_item.setBackground(QColor("#fff3cd"))  # Light yellow
            self.builds_table.setItem(row, 2, status_item)
            
            # Size
            size = build.get("size", 0)
            size_text = f"{size / (1024*1024):.1f} MB" if size > 0 else "Unknown"
            self.builds_table.setItem(row, 3, QTableWidgetItem(size_text))
            
            # Date
            self.builds_table.setItem(row, 4, QTableWidgetItem(build.get("date", "")))
            
            # Actions
            actions_widget = self._create_actions_widget(build)
            self.builds_table.setCellWidget(row, 5, actions_widget)
            
            # Share
            share_widget = self._create_share_widget(build)
            self.builds_table.setCellWidget(row, 6, share_widget)
            
    def _create_actions_widget(self, build: dict) -> QWidget:
        """Create the actions widget for a build row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # Download button
        download_btn = QPushButton("↓")
        download_btn.setToolTip("Download build")
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        download_btn.clicked.connect(lambda: self._handle_download(build))
        layout.addWidget(download_btn)
        
        # Upload button (only if downloaded)
        if build.get("status") == "downloaded":
            upload_btn = QPushButton("↑")
            upload_btn.setToolTip("Upload build")
            upload_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            upload_btn.clicked.connect(lambda: self._handle_upload(build))
            layout.addWidget(upload_btn)
        
        # Install button (only if downloaded)
        if build.get("status") == "downloaded":
            install_btn = QPushButton("▶")
            install_btn.setToolTip("Install build")
            install_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: #212529;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
            install_btn.clicked.connect(lambda: self._handle_install(build))
            layout.addWidget(install_btn)
        
        layout.addStretch()
        return widget
        
    def _create_share_widget(self, build: dict) -> QWidget:
        """Create the share widget for a build row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Share button (only if uploaded)
        if build.get("status") == "uploaded":
            share_btn = QPushButton("🔗")
            share_btn.setToolTip("Share build URL")
            share_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            share_btn.clicked.connect(lambda: self._handle_share(build))
            layout.addWidget(share_btn)
        
        layout.addStretch()
        return widget
        
    def _handle_download(self, build: dict):
        """Handle download button click."""
        try:
            platform = self.platform_combo.currentText().lower()
            build_id = build.get("id", "")
            if platform == "android":
                self.android_controller.download_build(build_id, platform)
            elif platform == "ios":
                self.ios_controller.download_build(build_id, platform)
        except Exception as e:
            self._handle_error(f"Failed to download build: {e}")
            
    def _handle_upload(self, build: dict):
        """Handle upload button click."""
        try:
            platform = self.platform_combo.currentText().lower()
            build_id = build.get("id", "")
            local_path = build.get("local_path", "")
            if platform == "android":
                self.android_controller.upload_build(build_id, local_path, platform)
            elif platform == "ios":
                self.ios_controller.upload_build(build_id, local_path, platform)
        except Exception as e:
            self._handle_error(f"Failed to upload build: {e}")
            
    def _handle_install(self, build: dict):
        """Handle install button click."""
        try:
            build_id = build.get("id", "")
            if self.platform_combo.currentText().lower() == "android":
                self.android_controller.install_requested.emit(build_id)
            else:
                self.ios_controller.install_requested.emit(build_id)
        except Exception as e:
            self._handle_error(f"Failed to install build: {e}")
            
    def _handle_share(self, build: dict):
        """Handle share button click."""
        try:
            build_id = build.get("id", "")
            if self.platform_combo.currentText().lower() == "android":
                self.android_controller.share_requested.emit(build_id)
            else:
                self.ios_controller.share_requested.emit(build_id)
        except Exception as e:
            self._handle_error(f"Failed to share build: {e}")
        
    def _setup_status_bar(self):
        """Set up status bar for displaying error messages."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create permanent widget for error messages
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_bar.addPermanentWidget(self.error_label)
        
        # Create temporary widget for status messages
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_bar.addWidget(self.status_label)
        
    def _handle_error(self, error_message: str):
        """Central error handler for all controllers."""
        logger.error(f"Error occurred: {error_message}")
        
        # Show error in status bar
        self.error_label.setText(error_message)
        
        # Show error dialog with details
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("An error occurred")
        error_dialog.setInformativeText(error_message)
        error_dialog.setDetailedText(f"Error details:\n{error_message}")
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec()
        
    def show_status(self, message: str, timeout: int = 5000):
        """Show a temporary status message."""
        self.status_label.setText(message)
        self.status_bar.showMessage(message, timeout)
        
    def clear_error(self):
        """Clear the error message from the status bar."""
        self.error_label.clear()
        
    def _connect_signals(self):
        """Connect all controller signals to their handlers."""
        # Connect error signals from all controllers
        if hasattr(self, 'main_controller'):
            self.main_controller.error_occurred.connect(self._handle_error)
        if hasattr(self, 'log_controller'):
            self.log_controller.error_occurred.connect(self._handle_error)
        if hasattr(self, 'build_controller'):
            self.build_controller.error_occurred.connect(self._handle_error)
            
        # Connect status signals
        if hasattr(self, 'main_controller'):
            self.main_controller.build_list_updated.connect(
                lambda builds: self.show_status(f"Fetched {len(builds)} builds")
            )
            self.main_controller.build_status_changed.connect(
                lambda build_id, status: self.show_status(f"Build {build_id}: {status}")
            )

        # Connect build operation signals
        if hasattr(self, 'build_controller'):
            self.build_controller.build_downloaded.connect(self._handle_build_download)
            self.build_controller.build_uploaded.connect(self._handle_build_upload)
            self.build_controller.upload_retry.connect(self._handle_upload_retry)
            
            # Show progress dialog for downloads
            self.build_controller.download_started.connect(
                lambda build_id: self._show_progress_dialog(f"Downloading build {build_id}")
            )
            
            # Show progress dialog for uploads
            self.build_controller.upload_started.connect(
                lambda build_id: self._show_progress_dialog(f"Uploading build {build_id}")
            )
            
            # Update progress for downloads
            self.build_controller.download_progress.connect(
                lambda build_id, progress: self._progress_dialog.update_progress(
                    progress, f"Downloading build {build_id}: {progress}%"
                ) if self._progress_dialog else None
            )
            
            # Update progress for uploads
            self.build_controller.upload_progress.connect(
                lambda build_id, progress: self._progress_dialog.update_progress(
                    progress, f"Uploading build {build_id}: {progress}%"
                ) if self._progress_dialog else None
            )

    refresh_builds = Signal()
    download_selected = Signal(list)
    upload_selected = Signal(list)

    def _show_progress_dialog(self, title: str) -> ProgressDialog:
        """Show progress dialog and return it."""
        if self._progress_dialog:
            self._progress_dialog.close()
        self._progress_dialog = ProgressDialog(title, self)
        self._progress_dialog.show()
        return self._progress_dialog
        
    def _handle_build_download(self, build_id: str, local_path: str):
        """Handle build download completion."""
        if self._progress_dialog:
            self._progress_dialog.update_progress(100, f"Downloaded to: {local_path}")
            QTimer.singleShot(2000, self._progress_dialog.close)
        self.show_status(f"Downloaded build {build_id}")
        
    def _handle_build_upload(self, build_id: str, blob_url: str):
        """Handle build upload completion."""
        if self._progress_dialog:
            self._progress_dialog.update_progress(100, f"Uploaded to: {blob_url}")
            QTimer.singleShot(2000, self._progress_dialog.close)
        self.show_status(f"Uploaded build {build_id}")
        
    def _handle_upload_retry(self, build_id: str, local_path: str, attempt: int):
        """Handle upload retry attempt."""
        if self._progress_dialog:
            self._progress_dialog.update_progress(
                0, f"Retrying upload of build {build_id} (attempt {attempt})"
            )
        self.show_status(f"Retrying upload of build {build_id} (attempt {attempt})") 