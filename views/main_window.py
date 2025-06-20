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
    QStatusBar, QProgressBar, QDialog, QLineEdit, QSizePolicy
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
from datetime import datetime
import os

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
    
    refresh_requested = Signal()
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        # Set up build managers first
        self._setup_build_managers()
        
        # Initialize webapps and selected_webapp before controllers
        self.webapps = self._load_webapps()
        self.selected_webapp = self.webapps[0] if self.webapps else None
        
        # Initialize controllers
        self._setup_controllers()
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
        
        self.health_statuses = {}  # Store health statuses
        self.history_manager = HistoryManager()
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
        
        # Create tab widget for build views
        tab_widget = QTabWidget()
        tab_widget.addTab(self.android_view, "Android Builds")
        tab_widget.addTab(self.ios_view, "iOS Builds")
        main_layout.addWidget(tab_widget)
        
        # Create bottom panels for health status and logs
        self._create_bottom_panels(main_layout)
        
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
        
        # Platform selector and actions
        controls_layout = QHBoxLayout()
        
        # Refresh button
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        refresh_button.clicked.connect(self.refresh_builds)
        controls_layout.addWidget(refresh_button)
        
        controls_layout.addStretch()
        
        # Add controls to header
        header_layout.addLayout(controls_layout)
        
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
        
        parent_layout.addWidget(controls_widget)
        
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
        self.log_area.setMinimumHeight(200)  # Set minimum height for better visibility
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
        
        # Set the log group to expand vertically
        log_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        bottom_layout.addWidget(log_group, 1)  # Give logs more space
        
        parent_layout.addWidget(bottom_widget)
        
    def _connect_ui_signals(self):
        """Connect UI signals."""
        # Connect search and filter signals
        self.search_input.textChanged.connect(self._on_search_changed)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        
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
        self.health_controller.error_occurred.connect(self._append_log)  # Connect error signal to log
        self.health_controller.start_monitoring()  # Start health monitoring
        
        # Log controller
        self.log_controller = LogController(self.selected_webapp)
        self.log_controller.log_message.connect(self._append_log)
        
        # Database controller (for error browser functionality)
        self.database_model = DatabaseModel()
        self.database_view = DatabaseView()
        self.database_controller = DatabaseController(self.database_model, self.database_view)
        
        # Build controllers
        self.android_controller = BuildController(self.android_model, self.android_view)
        self.ios_controller = BuildController(self.ios_model, self.ios_view)
        
        # Connect upload signals
        self.android_view.upload_requested.connect(self._handle_android_upload)
        self.ios_view.upload_requested.connect(self._handle_ios_upload)
        
    def _setup_build_managers(self):
        """Set up build managers and controllers."""
        # Create models
        self.android_model = BuildManager()
        self.ios_model = BuildManager()
        
        # Initialize Azure for both models
        try:
            container_name = os.getenv("AZURE_STORAGE_CONTAINER", "builds")
            self.android_model.initialize_azure(container_name)
            self.ios_model.initialize_azure(container_name)
        except Exception as e:
            self._handle_error(f"Failed to initialize Azure service: {e}")
        
        # Create build views for each platform
        self.android_view = BuildView("android")
        self.ios_view = BuildView("ios")
        
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
        
        # Add Health Check Settings action
        health_settings_action = settings_menu.addAction("Health Check Settings")
        health_settings_action.triggered.connect(self.show_health_settings)
        
        settings_menu.addSeparator()
        
        sp_info_action = QAction("View SP Info", self)
        sp_info_action.triggered.connect(self._show_sp_info)
        settings_menu.addAction(sp_info_action)
        
    def _update_health_status(self, webapp: str, is_healthy: bool):
        """Update health status display."""
        # Update the status in our dictionary
        self.health_statuses[webapp] = is_healthy
        
        # Create the status text with all services
        status_lines = []
        for app, healthy in self.health_statuses.items():
            color = "#28a745" if healthy else "#dc3545"  # Bootstrap success/danger colors
            status = "Healthy" if healthy else "Unhealthy"
            status_lines.append(f'<div style="margin: 4px 0;"><span style="color: {color};">●</span> {app}: {status}</div>')
        
        # Update the label with all statuses
        self.health_status.setText(f"""
            <div style="
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 8px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
                font-size: 13px;
                line-height: 1.4;
            ">
                {"".join(status_lines)}
            </div>
        """)
        
    def _append_log(self, message: str):
        """Append message to log area with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_area.append(formatted_message)
        # Auto-scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
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
        
    def refresh_builds(self, *_):
        """Refresh build list for both platforms."""
        try:
            # Refresh both Android and iOS builds
            self.android_controller.fetch_builds("android", force_refresh=True)
            self.ios_controller.fetch_builds("ios", force_refresh=True)
            self.show_status("Refreshing builds...")
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

    def show_health_settings(self):
        """Show health check settings dialog."""
        from views.health_settings_dialog import HealthSettingsDialog
        dialog = HealthSettingsDialog(self.health_controller.model, self)
        if dialog.exec() == QDialog.Accepted:
            # Trigger a health check refresh
            self.health_controller.start_monitoring()
            self._append_log("Health check settings updated")

    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #dc3545;")  # Bootstrap danger color
        self.status_bar.addPermanentWidget(self.error_label)
        
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
            
        # Connect build operation signals
        if hasattr(self, 'android_controller'):
            self.android_controller.builds_fetched.connect(self._handle_builds_fetched)
            self.android_controller.build_downloaded.connect(self._handle_build_download)
            self.android_controller.build_uploaded.connect(self._handle_build_upload)
            self.android_controller.upload_retry.connect(self._handle_upload_retry)
            
        if hasattr(self, 'ios_controller'):
            self.ios_controller.builds_fetched.connect(self._handle_builds_fetched)
            self.ios_controller.build_downloaded.connect(self._handle_build_download)
            self.ios_controller.build_uploaded.connect(self._handle_build_upload)
            self.ios_controller.upload_retry.connect(self._handle_upload_retry)
            
    def _handle_builds_fetched(self, builds):
        """Handle fetched builds."""
        # The builds will be automatically updated in their respective views
        # since the controllers emit the builds_fetched signal
        self.show_status(f"Fetched {len(builds)} builds")
        
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