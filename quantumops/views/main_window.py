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
    QStatusBar, QProgressBar, QDialog, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QSettings
from PySide6.QtGui import QColor, QPalette, QAction
from quantumops.controllers.log_controller import LogController
from quantumops.controllers.health_controller import HealthController
from quantumops.controllers.database_controller import DatabaseController
from quantumops.azure_webapp import AzureWebApp
from quantumops.models.database import Database
from quantumops.views.database_view import DatabaseView
from quantumops.views.build_view import BuildView
from quantumops.models.build_manager import BuildManager
from quantumops.controllers.build_controller import BuildController
from ..models.history_manager import HistoryManager
from .history_dialog import HistoryDialog
from .preview_dialog import PreviewDialog
from .layouts import ClassicTabbedLayout, SplitViewLayout, DashboardLayout
from quantumops.views.azure_config_dialog import AzureConfigDialog
from quantumops.views.status_indicator import StatusIndicator
from quantumops.views.progress_dialog import ProgressDialog
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window for QuantumOps."""
    
    def __init__(self, web_apps: list):
        """Initialize main window.
        
        Args:
            web_apps: List of web app names
        """
        super().__init__()
        self.web_apps = web_apps
        self.settings = QSettings("RosieVision", "QuantumOps")
        
        # Initialize controllers
        self._init_controllers()
        
        # Setup UI
        self._init_ui()
        self._setup_menu()
        self._setup_status_bar()
        
        # Load initial data
        self._load_data()
    
    def _init_controllers(self):
        """Initialize controllers."""
        # Create database instance
        db_config = {
            "dbname": self.settings.value("database/name", "quantumops"),
            "user": self.settings.value("database/user", "postgres"),
            "password": self.settings.value("database/password", "postgres"),
            "host": self.settings.value("database/host", "localhost")
        }
        db = Database(db_config)
        
        # Create controllers
        self._db_controller = DatabaseController(db)
        self._build_controller = BuildController(self._db_controller)
        
        # Connect signals
        self._db_controller.connection_status_changed.connect(self._handle_db_status)
        self._db_controller.error_occurred.connect(self._handle_error)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("QuantumOps")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add webapp and platform selectors at the top (always present)
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Azure Web App:"))
        self.web_app_combo = QComboBox()
        self.web_app_combo.addItems(self.web_apps)
        self.web_app_combo.currentTextChanged.connect(self._handle_web_app_change)
        selector_layout.addWidget(self.web_app_combo)
        selector_layout.addWidget(QLabel("Platform:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Android", "iOS"])
        self.platform_combo.currentTextChanged.connect(self._handle_platform_change)
        selector_layout.addWidget(self.platform_combo)
        selector_layout.addStretch()
        selector_widget = QWidget()
        selector_widget.setLayout(selector_layout)
        main_layout.addWidget(selector_widget)

        # Create a QStackedWidget for the main content area
        self._layout_stack = QStackedWidget()
        self._layouts = {}
        classic_layout = ClassicTabbedLayout()
        self._layouts['classic'] = classic_layout
        self._layout_stack.addWidget(classic_layout)
        split_layout = SplitViewLayout()
        self._layouts['split'] = split_layout
        self._layout_stack.addWidget(split_layout)
        dashboard_layout = DashboardLayout()
        self._layouts['dashboard'] = dashboard_layout
        self._layout_stack.addWidget(dashboard_layout)
        main_layout.addWidget(self._layout_stack, 1)

        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Create menu bar
        self._create_menu_bar()
        
        # Connect button signals (if present in layouts)
        # (Assume ClassicTabbedLayout has refresh_button, download_button, upload_button)
        if hasattr(classic_layout, 'refresh_button'):
            classic_layout.refresh_button.clicked.connect(self._handle_refresh)
        if hasattr(classic_layout, 'download_button'):
            classic_layout.download_button.clicked.connect(self._handle_download)
        if hasattr(classic_layout, 'upload_button'):
            classic_layout.upload_button.clicked.connect(self._handle_upload)

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        refresh_action = file_menu.addAction("Refresh")
        refresh_action.triggered.connect(self._handle_refresh)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        history_action = view_menu.addAction("Build History")
        history_action.triggered.connect(self.show_history)
        
        # Layout menu
        layout_menu = menubar.addMenu("Layout")
        classic_action = layout_menu.addAction("Classic Tabbed")
        classic_action.triggered.connect(lambda: self.switch_layout("classic"))
        split_action = layout_menu.addAction("Split View")
        split_action.triggered.connect(lambda: self.switch_layout("split"))
        dashboard_action = layout_menu.addAction("Dashboard")
        dashboard_action.triggered.connect(lambda: self.switch_layout("dashboard"))
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        sp_info_action = QAction("View SP Info", self)
        sp_info_action.triggered.connect(self._show_sp_info)
        settings_menu.addAction(sp_info_action)
        
    def _setup_menu(self):
        """Setup menu bar."""
        # Create menu bar
        menu_bar = self.menuBar()
        
        # Create File menu
        file_menu = menu_bar.addMenu("File")
        
        # Add actions
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._handle_refresh)
        file_menu.addAction(refresh_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Create Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        
        azure_action = QAction("Azure Configuration", self)
        azure_action.triggered.connect(self._handle_azure_config)
        settings_menu.addAction(azure_action)
        
        # Create Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._handle_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add status indicator
        self.status_indicator = StatusIndicator()
        self.status_bar.addPermanentWidget(self.status_indicator)
    
    def _load_data(self):
        """Load initial data."""
        self._handle_refresh()
    
    def _handle_web_app_change(self, web_app: str):
        """Handle web app change.
        
        Args:
            web_app: Selected web app
        """
        self._handle_refresh()
    
    def _handle_platform_change(self, platform: str):
        """Handle platform change.
        
        Args:
            platform: Selected platform
        """
        self._handle_refresh()
    
    def _handle_refresh(self):
        """Handle refresh action."""
        try:
            platform = self.platform_combo.currentText().lower()
            builds = self._build_controller.get_builds(platform)
            # TODO: Update build list with builds
        except Exception as e:
            self._handle_error(str(e))
    
    def _handle_upload(self):
        """Handle upload action."""
        # TODO: Implement upload functionality
        pass
    
    def _handle_download(self):
        """Handle download action."""
        # TODO: Implement download functionality
        pass
    
    def _handle_azure_config(self):
        """Handle Azure configuration action."""
        dialog = AzureConfigDialog(self)
        if dialog.exec():
            # TODO: Update Azure configuration
            pass
    
    def _handle_about(self):
        """Handle about action."""
        QMessageBox.about(
            self,
            "About QuantumOps",
            "QuantumOps - Mobile Build Manager\n\n"
            "Version 1.0.0\n"
            "Copyright © 2024 Rosie Vision"
        )
    
    def _handle_db_status(self, connected: bool, message: str):
        """Handle database status change.
        
        Args:
            connected: Whether connected to database
            message: Status message
        """
        self.status_indicator.set_status("connected" if connected else "disconnected")
        self.statusBar().showMessage(message)
    
    def _handle_error(self, message: str):
        """Handle error.
        
        Args:
            message: Error message
        """
        QMessageBox.critical(self, "Error", message)
        logger.error(message)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up resources
        self._db_controller.close()
        event.accept()
        
    def show_history(self):
        """Show history dialog."""
        dialog = HistoryDialog(self.history_manager, self)
        dialog.exec()
        
    def show_preview(self, item):
        """Show preview dialog."""
        row = item.row()
        build_id = self.build_table.item(row, 0).text()
        platform = self.platform_combo.currentText().lower()  # Convert to lowercase to match build view platform
        version = self.build_table.item(row, 1).text()
        
        dialog = PreviewDialog(build_id, platform, version, self)
        if dialog.exec():
            # Record preview in history
            self.history_manager.record_share(
                build_id=build_id,
                platform=platform,
                version=version,
                status="success",
                share_url=dialog.share_url
            )
            
    def _show_sp_info(self):
        """Show service principal info dialog."""
        # TODO: Implement SP info dialog
        pass
        
    def switch_layout(self, layout_name):
        """Switch the main content area to the selected layout."""
        if layout_name in self._layouts:
            idx = list(self._layouts.keys()).index(layout_name)
            self._layout_stack.setCurrentIndex(idx)
        else:
            logger.error(f"Unknown layout: {layout_name}")

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

    def switch_layout(self, layout_name):
        """Switch the main content area to the selected layout."""
        if layout_name in self._layouts:
            idx = list(self._layouts.keys()).index(layout_name)
            self._layout_stack.setCurrentIndex(idx)
        else:
            logger.error(f"Unknown layout: {layout_name}")

    def _load_webapps(self):
        config_path = Path("config/webapps.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return [] 