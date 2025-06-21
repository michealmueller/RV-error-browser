"""
Main window view for QuantumOps.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from azure_webapp import AzureWebApp
from controllers.build_controller import BuildController
from controllers.database_controller import DatabaseController
from controllers.health_controller import HealthController
from controllers.log_controller import LogController
from models.build_manager import BuildManager
from models.database import DatabaseModel
from models.history_manager import HistoryManager
from services.azure_service import AzureService
from views.build_view import BuildView
from views.database_view import DatabaseView

from .history_dialog import HistoryDialog

logger = logging.getLogger(__name__)


class StatusIndicator(QLabel):
    """Custom widget for displaying health status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.set_status(False)

    def set_status(self, is_healthy: bool) -> None:
        """Set the status indicator color."""
        color = (
            QColor("#28a745") if is_healthy else QColor("#dc3545")
        )  # Bootstrap success/danger colors
        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {color.name()};
                border-radius: 6px;
                border: 1px solid #dee2e6;
            }}
        """
        )


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

        # Core application attributes
        self.azure_service = AzureService()
        self.webapps = self._load_webapps()
        self.selected_webapp = self.webapps[0] if self.webapps else None
        self.all_versions = set()
        self.health_statuses = {}
        self.history_manager = HistoryManager()
        self._progress_dialog = None

        # Set up the UI, create controllers, and then connect signals
        self._init_ui()
        self._setup_controllers()
        self._connect_signals()

        logger.info("Main window initialized")
        self.log_controller.add_log("Application started successfully.", "INFO")

        # Start monitoring and fetch initial data
        self.health_controller.start_monitoring()
        self.refresh_builds()

        # Adjust window size after initial data load
        QTimer.singleShot(1000, self._adjust_window_size)

    def _init_ui(self):
        """Initialize the UI components with a simplified, user-friendly design."""
        self.setWindowTitle("QuantumOps - Mobile Build Manager")
        self.setMinimumSize(1400, 900)

        # Set up build views before creating main content
        self._setup_build_managers()

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Create and set up the main content
        self.main_splitter = self._create_main_content()
        main_layout.addWidget(self.main_splitter)

        # Set application-wide stylesheet for light theme
        self.setStyleSheet(
            """
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
        """
        )

        # Setup status bar and menu bar
        self._setup_status_bar()
        self._create_menu_bar()

    def _create_main_content(self) -> QSplitter:
        """Create the main content area with builds table and controls."""
        self.main_splitter = QSplitter(Qt.Vertical)

        # Top section for controls and build views
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(15)

        self._create_controls_section(top_layout)

        # Horizontal splitter for Android and iOS views
        build_splitter = QSplitter(Qt.Horizontal)

        # Android view container
        android_container = QWidget()
        android_layout = QVBoxLayout(android_container)
        android_layout.setContentsMargins(0, 0, 0, 0)
        android_label = QLabel("Android Builds")
        android_label.setStyleSheet("font-weight: bold; padding: 5px;")
        android_layout.addWidget(android_label)
        android_layout.addWidget(self.android_view)
        build_splitter.addWidget(android_container)

        # iOS view container
        ios_container = QWidget()
        ios_layout = QVBoxLayout(ios_container)
        ios_layout.setContentsMargins(0, 0, 0, 0)
        ios_label = QLabel("iOS Builds")
        ios_label.setStyleSheet("font-weight: bold; padding: 5px;")
        ios_layout.addWidget(ios_label)
        ios_layout.addWidget(self.ios_view)
        build_splitter.addWidget(ios_container)

        top_layout.addWidget(build_splitter)

        # Bottom section for health status and logs
        self._create_bottom_panels()

        self.main_splitter.addWidget(top_widget)
        self.main_splitter.addWidget(self.bottom_panels)

        # Set initial sizes for the main splitter
        self.main_splitter.setSizes([600, 200])
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(1, False)

        return self.main_splitter

    def _create_controls_section(self, parent_layout):
        """Create the controls section with search and filters."""
        controls_group = QGroupBox("Controls")
        controls_group.setMaximumHeight(
            100
        )  # Constrain the height of the controls area
        controls_layout = QHBoxLayout(controls_group)
        controls_layout.setContentsMargins(10, 10, 10, 10)

        # Search input
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold; color: #34495e;")
        controls_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search builds by ID, version, or status..."
        )
        self.search_input.setStyleSheet(
            """
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
        """
        )
        controls_layout.addWidget(self.search_input, 1)  # Give it more space

        # Version filter
        version_label = QLabel("Version:")
        version_label.setStyleSheet(
            "font-weight: bold; color: #34495e; margin-left: 15px;"
        )
        controls_layout.addWidget(version_label)

        self.version_filter = QComboBox()
        self.version_filter.addItem("All Versions", "")
        self.version_filter.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
                min-width: 120px;
            }
        """
        )
        controls_layout.addWidget(self.version_filter)

        # Status filter
        status_label = QLabel("Status:")
        status_label.setStyleSheet(
            "font-weight: bold; color: #34495e; margin-left: 15px;"
        )
        controls_layout.addWidget(status_label)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", "")
        self.status_filter.addItem("Finished", "finished")
        self.status_filter.addItem("Canceled", "canceled")
        self.status_filter.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
                min-width: 120px;
            }
        """
        )
        controls_layout.addWidget(self.status_filter)
        status_label.setVisible(False)
        self.status_filter.setVisible(False)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background: white;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """
        )
        controls_layout.addWidget(self.refresh_button)

        parent_layout.addWidget(controls_group)

    def _create_bottom_panels(self):
        """Create the bottom panels for health status and logs."""
        self.bottom_panels = QWidget()
        bottom_layout = QHBoxLayout(self.bottom_panels)
        bottom_layout.setSpacing(15)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        health_container = QWidget()
        health_layout = QVBoxLayout(health_container)
        health_layout.setSpacing(10)

        # RosieVision health status panel
        rosievision_health_group = QGroupBox("RosieVision Health")
        rosievision_health_layout = QVBoxLayout(rosievision_health_group)
        self.rosievision_health_status = QLabel("Checking...")
        self.rosievision_health_status.setStyleSheet(
            "padding: 10px; background-color: #f8f9fa; border-radius: 4px;"
        )
        self.rosievision_health_status.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        rosievision_health_layout.addWidget(self.rosievision_health_status)
        health_layout.addWidget(rosievision_health_group)

        # ProjectFlow health status panel
        projectflow_health_group = QGroupBox("ProjectFlow Health")
        projectflow_health_layout = QVBoxLayout(projectflow_health_group)
        self.projectflow_health_status = QLabel("Checking...")
        self.projectflow_health_status.setStyleSheet(
            "padding: 10px; background-color: #f8f9fa; border-radius: 4px;"
        )
        self.projectflow_health_status.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        projectflow_health_layout.addWidget(self.projectflow_health_status)
        health_layout.addWidget(projectflow_health_group)

        bottom_layout.addWidget(health_container)

        # Log panel
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout(log_group)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        log_layout.addWidget(self.log_area)
        bottom_layout.addWidget(log_group, 1)  # Give logs more space

    def _setup_controllers(self):
        """Set up the controllers."""
        # Main controllers
        self.log_controller = LogController(self.log_area)
        self.health_controller = HealthController(self.webapps, self)

        # Build controllers
        self.android_build_controller = BuildController(
            self.android_build_manager, self.android_view
        )
        self.ios_build_controller = BuildController(
            self.ios_build_manager, self.ios_view
        )

        # Database controller and view
        self.db_model = DatabaseModel()
        self.db_view = DatabaseView()
        self.db_controller = DatabaseController(self.db_model, self.db_view)

    def _connect_signals(self):
        """Connect all signals after UI and controllers are initialized."""
        # UI component signals
        self.refresh_button.clicked.connect(self.refresh_builds)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.version_filter.currentIndexChanged.connect(self._on_search_changed)

        # Menu actions
        self.settings_action.triggered.connect(self.show_health_settings)
        self.error_browser_action.triggered.connect(self.show_error_browser)

        # Health controller signals
        self.health_controller.status_updated.connect(self._update_health_status)
        self.health_controller.error_occurred.connect(
            lambda error: self.log_controller.add_log(error, "ERROR")
        )

        # Build controller signals
        self.android_build_controller.builds_fetched.connect(
            self._update_version_filter
        )
        self.ios_build_controller.builds_fetched.connect(self._update_version_filter)
        self.android_build_controller.error_occurred.connect(self._handle_error)
        self.ios_build_controller.error_occurred.connect(self._handle_error)

    def _on_search_changed(self):
        """Handle changes in search or filter inputs."""
        filters = {
            "search": self.search_input.text(),
            "version": self.version_filter.currentData() or "",
        }
        self.android_build_manager.filter_builds("android", filters)
        self.ios_build_manager.filter_builds("ios", filters)

    def _setup_build_managers(self):
        """Set up the build managers."""
        # Create models
        self.android_build_manager = BuildManager(self.azure_service)
        self.ios_build_manager = BuildManager(self.azure_service)

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

        self.error_browser_action = view_menu.addAction("Error Browser")

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        # Add Health Check Settings action
        self.settings_action = settings_menu.addAction("Health Check Settings")

        settings_menu.addSeparator()

        sp_info_action = QAction("View SP Info", self)
        sp_info_action.triggered.connect(self._show_sp_info)
        settings_menu.addAction(sp_info_action)

    def _update_health_status(self, webapp: str, is_healthy: bool):
        """Update health status in the UI."""
        self.health_statuses[webapp] = is_healthy

        rosievision_html = ""
        projectflow_html = ""

        for app, healthy in sorted(self.health_statuses.items()):
            color = "#28a745" if healthy else "#dc3545"
            status_text = "Healthy" if healthy else "Unhealthy"
            status_line = f'<div><b>{app}:</b> <span style="color: {color};">{status_text}</span></div>'

            if "rosievision" in app.lower() or "rv-" in app.lower():
                rosievision_html += status_line
            elif "projectflow" in app.lower() or "pf-" in app.lower():
                projectflow_html += status_line

        self.rosievision_health_status.setText(
            rosievision_html if rosievision_html else "Checking..."
        )
        self.projectflow_health_status.setText(
            projectflow_html if projectflow_html else "Checking..."
        )

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

    def show_error_browser(self):
        """Show the error browser dialog."""
        self.db_view.show()

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
        self.db_controller.cleanup()
        self.health_controller.cleanup()
        self.android_build_controller.cleanup()
        self.ios_build_controller.cleanup()
        event.accept()

    def show_history(self):
        """Show history dialog."""
        dialog = HistoryDialog(self.history_manager, self)
        dialog.exec()

    def refresh_builds(self, *_):
        """Refresh build list for both platforms."""
        try:
            # Refresh both Android and iOS builds
            self.android_build_controller.fetch_builds()
            self.ios_build_controller.fetch_builds()
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
            "© 2024 Rosie Vision",
        )

    def _load_webapps(self) -> List[AzureWebApp]:
        """Load webapp configurations from webapps.json."""
        try:
            config_path = Path("config/webapps.json")
            if not config_path.exists():
                logger.warning(
                    "webapps.json not found. Health checks will rely on health_endpoints.json."
                )
                return []

            with open(config_path, "r") as f:
                webapp_data = json.load(f)

            webapps = []
            for data in webapp_data:
                # The from_dict method will now pull credentials from os.environ
                webapps.append(AzureWebApp.from_dict(data))
            return webapps
        except Exception as e:
            self._handle_error(f"Failed to load webapps from {config_path}: {e}")
            return []

    def _on_webapp_changed(self, idx):
        if 0 <= idx < len(self.webapps):
            self.selected_webapp = self.webapps[idx]
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
        self.log_controller.add_log(error_message, "ERROR")

        # Show error in status bar
        self.error_label.setText(error_message)

        # Show error dialog with details
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("An error occurred")
        error_dialog.setInformativeText(error_message)
        error_dialog.setDetailedText(f"Error details:\\n{error_message}")
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec()

    def show_status(self, message: str, timeout: int = 5000):
        """Show a temporary status message."""
        self.status_label.setText(message)
        self.status_bar.showMessage(message, timeout)

    def clear_error(self):
        """Clear the error message from the status bar."""
        self.error_label.clear()

    def _update_version_filter(self, builds: list):
        """Update the version filter with unique versions from builds."""
        current_versions = {
            build.get("appVersion") for build in builds if build.get("appVersion")
        }

        if not self.all_versions:
            self._adjust_window_size()

        if not current_versions.issubset(self.all_versions):
            self.all_versions.update(current_versions)

            # Repopulate the dropdown
            self.version_filter.clear()
            self.version_filter.addItem("All Versions", "")
            sorted_versions = sorted(list(self.all_versions), reverse=True)
            for version in sorted_versions:
                self.version_filter.addItem(version, version)

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

    def _adjust_window_size(self):
        """Adjust window size to fit the tables."""
        try:
            # Calculate the required width for both tables
            android_width = (
                self.android_view.table.horizontalHeader().length()
                + self.android_view.table.verticalHeader().width()
            )
            ios_width = (
                self.ios_view.table.horizontalHeader().length()
                + self.ios_view.table.verticalHeader().width()
            )

            # Account for the splitter handle
            total_width = android_width + ios_width + self.main_splitter.handleWidth()

            # Add some padding
            total_width += 50

            # Set the new minimum width and resize the window
            self.setMinimumWidth(total_width)
            self.resize(total_width, self.height())
        except Exception as e:
            logger.error(f"Error adjusting window size: {e}")

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
