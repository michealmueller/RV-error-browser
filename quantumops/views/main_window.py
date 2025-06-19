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
    QStatusBar, QProgressBar, QDialog
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QColor, QPalette, QAction
from quantumops.controllers.log_controller import LogController
from quantumops.controllers.health_controller import HealthController
from quantumops.controllers.database_controller import DatabaseController
from quantumops.azure_webapp import AzureWebApp
from quantumops.models.database import DatabaseModel
from quantumops.views.database_view import DatabaseView
from quantumops.views.build_view import BuildView
from quantumops.models.build_manager import BuildManager
from quantumops.controllers.build_controller import BuildController
from ..models.history_manager import HistoryManager
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
        color = QColor("#2ecc71") if is_healthy else QColor("#e74c3c")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color.name()};
                border-radius: 6px;
                border: 1px solid #2d2d2d;
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
        """Initialize the UI components."""
        self.setWindowTitle("QuantumOps")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create database tab
        self.database_model = DatabaseModel()
        self.database_view = DatabaseView()
        self.database_controller = DatabaseController(self.database_model, self.database_view)
        self.tab_widget.addTab(self.database_view, "Error Browser")
        
        # Create health check panel
        health_group = QGroupBox("Health Status")
        health_layout = QVBoxLayout(health_group)
        self.health_status = QLabel("Checking health...")
        health_layout.addWidget(self.health_status)
        
        # Create log area
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout(log_group)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        log_layout.addWidget(self.log_area)
        
        # Create splitter for health and log
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(health_group)
        splitter.addWidget(log_group)
        splitter.setSizes([200, 400])  # Initial sizes
        
        # Create build tabs
        self.android_tab = BuildView("android")
        self.ios_tab = BuildView("ios")
        
        # Add tabs
        self.tab_widget.addTab(self.android_tab, "Android Builds")
        self.tab_widget.addTab(self.ios_tab, "iOS Builds")
        
        # Add webapp selector
        webapp_layout = QHBoxLayout()
        webapp_layout.addWidget(QLabel("Azure Web App:"))
        self.webapp_combo = QComboBox()
        for webapp in self.webapps:
            label = f"{webapp['name']} ({webapp['resource_group']})"
            self.webapp_combo.addItem(label, webapp)
        self.webapp_combo.currentIndexChanged.connect(self._on_webapp_changed)
        webapp_layout.addWidget(self.webapp_combo)
        webapp_layout.addStretch()
        
        # Wrap webapp_layout in a QWidget
        webapp_widget = QWidget()
        webapp_widget.setLayout(webapp_layout)
        
        # Add widgets to main layout
        main_layout.addWidget(webapp_widget)
        main_layout.addWidget(self.tab_widget, 7)  # 70% of space
        main_layout.addWidget(splitter, 3)  # 30% of space
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Connect refresh button to signal
        self.refresh_button.clicked.connect(self.refresh_builds.emit)
        self.download_button.clicked.connect(self._emit_download_selected)
        self.upload_button.clicked.connect(self._emit_upload_selected)
        
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
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        sp_info_action = QAction("View SP Info", self)
        sp_info_action.triggered.connect(self._show_sp_info)
        settings_menu.addAction(sp_info_action)
        
    def _setup_controllers(self):
        """Set up controllers."""
        # Health controller
        self.health_controller = HealthController()
        self.health_controller.status_updated.connect(self._update_health_status)
        
        # Log controller
        self.log_controller = LogController(self.selected_webapp)
        self.log_controller.log_message.connect(self._append_log)
        
    def _setup_build_managers(self):
        """Set up build managers and controllers."""
        # Create models
        self.android_model = BuildManager()
        self.ios_model = BuildManager()
        
        # Create controllers
        self.android_controller = BuildController(self.android_model, self.android_tab)
        self.ios_controller = BuildController(self.ios_model, self.ios_tab)
        
        # Connect upload signals
        self.android_tab.upload_requested.connect(self._handle_android_upload)
        self.ios_tab.upload_requested.connect(self._handle_ios_upload)
        
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
        
    def _handle_android_upload(self, build_id: str, local_path: str):
        """Handle Android build upload request."""
        # TODO: Implement Azure upload
        self.statusBar().showMessage(f"Uploading Android build {build_id}...")
        
    def _handle_ios_upload(self, build_id: str, local_path: str):
        """Handle iOS build upload request."""
        # TODO: Implement Azure upload
        self.statusBar().showMessage(f"Uploading iOS build {build_id}...")
        
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
        
    def show_preview(self, item):
        """Show preview dialog."""
        row = item.row()
        build_id = self.build_table.item(row, 0).text()
        platform = self.platform_combo.currentText()
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
            
    def _emit_download_selected(self):
        selected = self._get_selected_build_ids()
        self.download_selected.emit(selected)
        
    def _emit_upload_selected(self):
        selected = self._get_selected_build_ids()
        self.upload_selected.emit(selected)
        
    def refresh_builds(self):
        """Refresh build list."""
        # Refresh logic here
        pass
        
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