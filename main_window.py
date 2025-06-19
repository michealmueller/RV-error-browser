"""
Main window and application logic for QuantumOps.
"""
import sys
import logging
from datetime import datetime, timezone, timedelta
import psycopg2
from psycopg2 import Error
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QTableWidget,
    QTableWidgetItem, QFormLayout, QComboBox, QMessageBox,
    QSplitter, QDialog, QMenuBar, QMenu, QDialogButtonBox, QTextEdit,
    QFrame, QTabWidget, QSizePolicy, QProgressBar, QFileDialog, QTreeWidget, QTreeWidgetItem, QStyle, QStatusBar, QGroupBox
)
from PySide6.QtCore import Qt, QSettings, QTimer, QThread, Signal, QObject, QMetaObject, Q_ARG, Slot, QResource, QDateTime
from PySide6.QtGui import QAction, QPalette, QColor, QFont, QTextCursor, QActionGroup, QPixmap
from PySide6.QtWidgets import QApplication
import subprocess
import json
import os
import shutil
from urllib.parse import urlparse, parse_qs
from azure.storage.blob import BlobClient
import requests
import re
import qdarktheme
from delegates import DetailsDelegate, format_details
from dialogs import ConnectionDialog
from quantumops import database
from quantumops import builds
import tempfile
from theming import get_current_brand_colors
import html
import time
import functools
import threading
from constants import (
    AZURE_TENANT_ID,
    AZURE_CLIENT_ID,
    AZURE_CLIENT_SECRET,
    AZURE_STORAGE_ACCOUNT,
    AZURE_STORAGE_CONTAINER,
    DB_CONNECTIONS
)
from utils import ensure_main_thread, log_azure_operation, log_database_operation
from azure_webapp import AzureWebApp
import gc
from logging_utils import append_terminal_line as log_util
from theming import apply_branding_theme

# Import and compile resources
from compile_resources import compile_resources
compile_resources()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_HEALTH_ENDPOINTS = [
    ("ProjectFlow Stage API", "https://stageapi.projectflow.ai/health"),
    ("RosieVision Dev API", "https://moapidev.rosievision.ai/health"),
    ("RosieVision Stage API", "https://moapistage.rosievision.ai/health"),
    ("RosieVision Prod API", "https://moapi.rosievision.ai/health"),
    ("ProjectFlow Dev API", "https://devapi.projectflow.ai/health"),
]

class UploadWorker(QObject):
    progress = Signal(int)
    finished = Signal(str, bool, str)  # url, success, error_msg

    def __init__(self, local_path, blob_name):
        super().__init__()
        self.local_path = local_path
        self.blob_name = blob_name
        self._chunk_size = 1024 * 1024  # 1MB chunks
        self._max_retries = 3
        self._retry_delay = 1  # seconds

    def run(self):
        try:
            url = self.upload_with_progress()
            self.finished.emit(url, True, "")
        except Exception as e:
            self.finished.emit("", False, str(e))
        finally:
            # Clean up any temporary resources
            gc.collect()

    def upload_with_progress(self):
        import os
        from azure.storage.blob import BlobServiceClient
        from azure.identity import ClientSecretCredential
        from azure.core.exceptions import AzureError
        import time

        tenant_id = os.environ["AZURE_TENANT_ID"]
        client_id = os.environ["AZURE_CLIENT_ID"]
        client_secret = os.environ["AZURE_CLIENT_SECRET"]
        storage_account = os.environ["AZURE_STORAGE_ACCOUNT"]
        container_name = os.environ["AZURE_STORAGE_CONTAINER"]

        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )

        blob_service_client = BlobServiceClient(
            f"https://{storage_account}.blob.core.windows.net",
            credential=credential
        )
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(self.blob_name)

        file_size = os.path.getsize(self.local_path)
        uploaded = 0

        def progress_hook(bytes_amount):
            nonlocal uploaded
            if bytes_amount is None:
                bytes_amount = 0
            try:
                uploaded += int(bytes_amount)
            except Exception:
                pass
            percent = int((uploaded / file_size) * 100) if file_size > 0 else 100
            percent = max(0, min(100, percent))
            self.progress.emit(percent)

        # Upload in chunks with retry logic
        with open(self.local_path, "rb") as data:
            for attempt in range(self._max_retries):
                try:
                    # Upload with chunking
                    blob_client.upload_blob(
                        data,
                        overwrite=True,
                        raw_response_hook=lambda r: progress_hook(r.context.get("upload_stream_current", 0)),
                        max_concurrency=4,  # Limit concurrent uploads
                        length=file_size
                    )
                    break
                except AzureError as e:
                    if attempt == self._max_retries - 1:
                        raise
                    time.sleep(self._retry_delay * (attempt + 1))
                    data.seek(0)  # Reset file pointer

        # Set blob metadata and tags
        try:
            now_epoch = str(int(time.time()))
            platform = "android" if self.blob_name.startswith("android-builds/") else "ios" if self.blob_name.startswith("ios-builds/") else "unknown"
            
            tags = {
                "uploaded-by": "QuantumOps",
                "platform": platform,
                "uploaded-on": now_epoch
            }
            metadata = {
                "uploaded-by": "QuantumOps",
                "platform": platform,
                "uploaded-on": now_epoch
            }

            try:
                blob_client.set_blob_tags(tags)
            except Exception as tag_exc:
                if "AuthorizationPermissionMismatch" in str(tag_exc):
                    logger.error(f"Failed to set blob tags for {self.blob_name}: {tag_exc}")
                    from quantumops.logging_utils import append_terminal_line
                    append_terminal_line(None, f"Failed to set blob tags: Permission denied. Please ensure your Azure identity has 'Storage Blob Data Contributor' or higher RBAC role.", "error", True)
                else:
                    logger.error(f"Failed to set blob tags for {self.blob_name}: {tag_exc}")

            try:
                blob_client.set_blob_metadata(metadata)
            except Exception as meta_exc:
                logger.error(f"Failed to set blob metadata for {self.blob_name}: {meta_exc}")

            logger.info(f"Set blob tags and metadata for {self.blob_name}: {tags}")
        except Exception as meta_exc:
            logger.error(f"Failed to set blob tags/metadata for {self.blob_name}: {meta_exc}")

        return blob_client.url

class LogStreamWorker(QThread):
    """Worker thread for streaming logs from Azure Web App."""
    log_received = Signal(str)
    error_occurred = Signal(str)
    finished = Signal()
    
    def __init__(self, azure_webapp: AzureWebApp, resource_group: str, web_app_name: str):
        super().__init__()
        self.azure_webapp = azure_webapp
        self.resource_group = resource_group
        self.web_app_name = web_app_name
        self.is_running = True
        self._log_buffer = []
        self._buffer_lock = threading.Lock()
        self._max_buffer_size = 1000
        
    def run(self):
        """Run the log streaming worker."""
        try:
            def log_callback(line: str):
                if not self.is_running:
                    return
                with self._buffer_lock:
                    self._log_buffer.append(line)
                    if len(self._log_buffer) > self._max_buffer_size:
                        self._log_buffer = self._log_buffer[-self._max_buffer_size:]
                self.log_received.emit(line)
            
            self.azure_webapp.stream_logs(
                self.resource_group,
                self.web_app_name,
                callback=log_callback
            )
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
            
    def stop(self):
        """Stop the log streaming worker."""
        self.is_running = False
        with self._buffer_lock:
            self._log_buffer.clear()
        self.wait()

class ApiHealthWorker(QObject):
    finished = Signal()
    status_update = Signal(str)
    
    def __init__(self, api_url):
        super().__init__()
        self.api_url = api_url
        self.is_running = True
    
    def run(self):
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                self.status_update.emit("up")
            else:
                self.status_update.emit("down")
        except Exception as e:
            self.status_update.emit("down")
        finally:
            self.finished.emit()
    
    def stop(self):
        self.is_running = False

class MainWindow(QMainWindow):
    main_thread_signal = Signal(object)

    def __init__(self):
        super().__init__()
        self.main_thread_signal.connect(lambda f: f())
        self.setWindowTitle("QuantumOps")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize Azure credentials
        self.azure_tenant_id = AZURE_TENANT_ID
        self.azure_client_id = AZURE_CLIENT_ID
        self.azure_client_secret = AZURE_CLIENT_SECRET
        self.azure_storage_account = AZURE_STORAGE_ACCOUNT
        self.azure_storage_container = AZURE_STORAGE_CONTAINER
        
        # Initialize database connections
        self.db_connections = DB_CONNECTIONS
        
        # Initialize Azure WebApp client
        self.azure_webapp = AzureWebApp(
            tenant_id=self.azure_tenant_id,
            client_id=self.azure_client_id,
            client_secret=self.azure_client_secret
        )
        
        # Initialize log streaming worker
        self.log_worker = None
        
        # Initialize memory management
        self._setup_memory_management()
        
        logger.info("Application started")
        self._setup_initial_state()
        self._setup_ui()
        logger.info("Application initialized successfully")

    def _setup_memory_management(self):
        """Initialize memory management settings and cleanup timers."""
        # Set up periodic garbage collection
        self.gc_timer = QTimer(self)
        self.gc_timer.timeout.connect(self._perform_gc)
        self.gc_timer.start(30000)  # Run every 30 seconds
        
        # Set up UI cleanup timer
        self.ui_cleanup_timer = QTimer(self)
        self.ui_cleanup_timer.timeout.connect(self._cleanup_ui_resources)
        self.ui_cleanup_timer.start(60000)  # Run every minute
        
        # Initialize resource tracking
        self._active_resources = set()
        self._resource_lock = threading.Lock()

    def _perform_gc(self):
        """Perform garbage collection and memory cleanup."""
        try:
            # Force garbage collection
            gc.collect()
            
            # Log memory usage
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            logger.debug(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            logger.error(f"Error during garbage collection: {e}")

    def _cleanup_ui_resources(self):
        """Clean up UI resources and temporary data."""
        try:
            # Clear old log entries
            if hasattr(self, 'log_viewer'):
                self._cleanup_log_viewer()
            
            # Clear old table data
            if hasattr(self, 'builds_table'):
                self._cleanup_builds_table()
            
            # Clear temporary files
            self._cleanup_temp_files()
            
        except Exception as e:
            logger.error(f"Error cleaning up UI resources: {e}")

    def _cleanup_log_viewer(self):
        """Clean up old log entries from the log viewer."""
        try:
            max_lines = 1000
            log_text = self.log_viewer.toPlainText()
            lines = log_text.split('\n')
            
            if len(lines) > max_lines:
                # Keep only the most recent lines
                lines = lines[-max_lines:]
                self.log_viewer.setPlainText('\n'.join(lines))
                
        except Exception as e:
            logger.error(f"Error cleaning up log viewer: {e}")

    def _cleanup_builds_table(self):
        """Clean up old data from the builds table."""
        try:
            # Keep only the most recent 100 rows
            max_rows = 100
            if self.builds_table.rowCount() > max_rows:
                self.builds_table.setRowCount(max_rows)
                
        except Exception as e:
            logger.error(f"Error cleaning up builds table: {e}")

    def _cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            temp_dir = tempfile.gettempdir()
            for file in os.listdir(temp_dir):
                if file.startswith('quantumops_'):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        # Remove files older than 1 hour
                        if time.time() - os.path.getmtime(file_path) > 3600:
                            os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Error removing temp file {file}: {e}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Stop all timers
            if hasattr(self, 'gc_timer'):
                self.gc_timer.stop()
            if hasattr(self, 'ui_cleanup_timer'):
                self.ui_cleanup_timer.stop()
            
            # Clean up log worker
            self._cleanup_log_thread()
            
            # Clean up UI resources
            self._cleanup_ui_resources()
            
            # Force final garbage collection
            gc.collect()
            
            # Accept the close event
            event.accept()
            
        except Exception as e:
            logger.error(f"Error during application close: {e}")
            event.accept()

    def _setup_initial_state(self):
        """Initialize application state variables."""
        try:
            # Track health check threads and workers
            self.api_health_threads: List[QThread] = []
            self.api_health_workers: List[Any] = []
            
            # Initialize API endpoints
            self.api_endpoints = [
                "https://stageapi.projectflow.ai/health",
                "https://moapidev.rosievision.ai/health",
                "https://moapistage.rosievision.ai/health",
                "https://moapi.rosievision.ai/health",
                "https://devapi.projectflow.ai/health"
            ]
            
            # Initialize other attributes
            self.connections: List[Dict[str, Any]] = []
            self.current_connection: Optional[Dict[str, Any]] = None
            self.log_thread: Optional[QThread] = None
            self.log_enabled = False
            self.eas_setup_complete = False
            self.streaming_azure_logs = False
            
            # Load settings and connections
            self.load_settings()
            self.connections = database.load_connections()
            
        except Exception as e:
            logger.error(f"Error initializing application state: {str(e)}")
            raise

    def _setup_ui(self):
        """Set up the main user interface."""
        try:
            self.setWindowTitle("QuantumOps")
            self.setMinimumSize(1200, 800)
            
            # Create main splitter
            main_splitter = QSplitter(Qt.Horizontal)
            
            # Setup left and right panels
            self._setup_health_panel(main_splitter)
            self._setup_tab_widget(main_splitter)
            
            # Set initial sizes (30% for health panel, 70% for tabs)
            main_splitter.setSizes([300, 700])
            
            # Set the splitter as the central widget
            self.setCentralWidget(main_splitter)
            
        except Exception as e:
            logger.error(f"Error setting up UI: {str(e)}")
            raise

    def _setup_timers(self):
        """Set up application timers."""
        try:
            # Log refresh timer
            self.log_timer = QTimer()
            self.log_timer.timeout.connect(self.refresh_logs)
            self.log_timer.start(2000)  # Refresh logs every 2 seconds
            
            # API health check timer
            self.api_health_timer = QTimer()
            self.api_health_timer.timeout.connect(self.check_api_health)
            self.api_health_timer.start(60000)  # Check every 60 seconds
            
        except Exception as e:
            logger.error(f"Error setting up timers: {str(e)}")
            raise

    def _log_startup(self):
        """Log application startup."""
        try:
            self.append_system_log("Application started", "info")
            logger.info("Application initialized successfully")
        except Exception as e:
            logger.error(f"Error logging startup: {str(e)}")
            # Don't raise here as this is not critical

    def _setup_health_panel(self, parent):
        """Set up the API health panel."""
        try:
            health_panel = QWidget()
            health_layout = QVBoxLayout()
            
            # API Health Header
            health_header = QLabel("API Health Status")
            health_header.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #ffffff;
                    padding: 10px;
                    background-color: #2d2d2d;
                    border-radius: 5px;
                }
            """)
            health_layout.addWidget(health_header)
            
            # API Status Container
            self.api_status_container = QWidget()
            self.api_status_layout = QVBoxLayout()
            self.api_status_container.setLayout(self.api_status_layout)
            self.api_status_container.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            health_layout.addWidget(self.api_status_container)
            
            # Last checked timestamp
            self.last_checked_label = QLabel("Last checked: Never")
            self.last_checked_label.setStyleSheet("color: #888888; font-size: 12px;")
            health_layout.addWidget(self.last_checked_label)
            
            health_panel.setLayout(health_layout)
            health_panel.setMinimumWidth(300)
            parent.addWidget(health_panel)
            
        except Exception as e:
            logger.error(f"Error setting up health panel: {str(e)}")
            raise

    def _setup_tab_widget(self, parent):
        """Set up the main tab widget."""
        try:
            tab_widget = QTabWidget()
            tab_widget.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #3d3d3d;
                    background-color: #1e1e1e;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    padding: 8px 16px;
                    border: 1px solid #3d3d3d;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                    border-bottom: 1px solid #1e1e1e;
                }
                QTabBar::tab:hover {
                    background-color: #3d3d3d;
                }
            """)
            
            # Add tabs
            self.setup_log_tab(tab_widget)
            self.setup_database_tab(tab_widget)
            
            parent.addWidget(tab_widget)
            
        except Exception as e:
            logger.error(f"Error setting up tab widget: {str(e)}")
            raise

    def setup_log_tab(self, tab_widget):
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        
        # Log Source Selection Panel
        source_panel = QGroupBox("Log Source Selection")
        source_panel.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 1em;
                padding: 10px;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        source_layout = QVBoxLayout()
        
        # Web App Selection
        webapp_layout = QHBoxLayout()
        webapp_label = QLabel("Web App:")
        webapp_label.setStyleSheet("color: #ffffff;")
        webapp_layout.addWidget(webapp_label)
        
        self.webapp_combo = QComboBox()
        self.webapp_combo.setMinimumWidth(250)
        self.webapp_combo.setToolTip("Select a web app to view its logs")
        self.webapp_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 5px;
                min-width: 250px;
                border-radius: 4px;
            }
            QComboBox:hover {
                border: 1px solid #4d4d4d;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        
        # Add the predefined web apps
        web_apps = [
            "RV-Dev-api",
            "RV-Staging-api",
            "PF-Dev-web",
            "PF-Dev-api",
            "PF-Staging-web",
            "PF-Staging-api"
        ]
        self.webapp_combo.addItems(web_apps)
        webapp_layout.addWidget(self.webapp_combo)
        
        # Fetch Logs Button
        self.fetch_logs_btn = QPushButton("Fetch Logs")
        self.fetch_logs_btn.setToolTip("Start fetching logs from the selected web app")
        self.fetch_logs_btn.clicked.connect(self.handle_fetch_azure_logs)
        self.fetch_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:disabled {
                background-color: #1d1d1d;
                color: #666666;
                border: 1px solid #2d2d2d;
            }
        """)
        webapp_layout.addWidget(self.fetch_logs_btn)
        webapp_layout.addStretch()
        
        # Add layouts to source layout
        source_layout.addLayout(webapp_layout)
        
        # Loading Indicator
        self.loading_spinner = QLabel()
        self.loading_spinner.setToolTip("Loading status")
        self.loading_spinner.hide()
        source_layout.addWidget(self.loading_spinner)
        
        # Status Label
        self.loading_status = QLabel()
        self.loading_status.setStyleSheet("color: #ffffff;")
        self.loading_status.hide()
        source_layout.addWidget(self.loading_status)
        
        source_panel.setLayout(source_layout)
        log_layout.addWidget(source_panel)
        
        # Log Source Log Window
        log_source_group = QGroupBox("Log Source")
        log_source_layout = QVBoxLayout()
        self.log_source_viewer = QTextEdit()
        self.log_source_viewer.setReadOnly(True)
        self.log_source_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 8px;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
        log_source_layout.addWidget(self.log_source_viewer)
        log_source_group.setLayout(log_source_layout)
        
        # System Log Window
        system_log_group = QGroupBox("System Log")
        system_log_layout = QVBoxLayout()
        self.system_log_viewer = QTextEdit()
        self.system_log_viewer.setReadOnly(True)
        self.system_log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 8px;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
        system_log_layout.addWidget(self.system_log_viewer)
        system_log_group.setLayout(system_log_layout)
        
        # Add log viewers to layout
        log_layout.addWidget(log_source_group)
        log_layout.addWidget(system_log_group)
        
        log_tab.setLayout(log_layout)
        tab_widget.addTab(log_tab, "Logs")
        
        # Initialize resource group combo box
        self.update_resource_group_combo()

    def setup_database_tab(self, tab_widget):
        """Set up the database tab with connection management and query functionality."""
        try:
            db_tab = QWidget()
            db_layout = QVBoxLayout()
            
            # Database connection selector
            connection_group = QGroupBox("Database Connection")
            connection_group.setStyleSheet("""
                QGroupBox {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    margin-top: 1em;
                    padding: 10px;
                }
                QGroupBox::title {
                    color: #ffffff;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }
            """)
            connection_layout = QVBoxLayout()
            
            # Connection selector
            selector_layout = QHBoxLayout()
            self.connection_combo = QComboBox()
            self.connection_combo.setStyleSheet("""
                QComboBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    padding: 5px;
                    min-width: 250px;
                    border-radius: 4px;
                }
                QComboBox:hover {
                    border: 1px solid #4d4d4d;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: url(down_arrow.png);
                    width: 12px;
                    height: 12px;
                }
            """)
            selector_layout.addWidget(QLabel("Database:"))
            selector_layout.addWidget(self.connection_combo)
            
            # Connection management buttons
            self.add_connection_btn = QPushButton("Add")
            self.add_connection_btn.clicked.connect(self.handle_add_connection)
            self.edit_connection_btn = QPushButton("Edit")
            self.edit_connection_btn.clicked.connect(self.handle_edit_connection)
            self.delete_connection_btn = QPushButton("Delete")
            self.delete_connection_btn.clicked.connect(self.handle_delete_connection)
            
            for btn in [self.add_connection_btn, self.edit_connection_btn, self.delete_connection_btn]:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #3d3d3d;
                        padding: 5px 10px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                    }
                """)
                selector_layout.addWidget(btn)
            
            selector_layout.addStretch()
            connection_layout.addLayout(selector_layout)
            
            # Connection details
            details_layout = QFormLayout()
            self.host_label = QLineEdit()
            self.port_label = QLineEdit()
            self.dbname_label = QLineEdit()
            self.user_label = QLineEdit()
            self.password_label = QLineEdit()
            self.password_label.setEchoMode(QLineEdit.Password)
            
            for field in [self.host_label, self.port_label, self.dbname_label, 
                         self.user_label, self.password_label]:
                field.setStyleSheet("""
                    QLineEdit {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #3d3d3d;
                        padding: 5px;
                        border-radius: 4px;
                    }
                    QLineEdit:hover {
                        border: 1px solid #4d4d4d;
                    }
                """)
            
            details_layout.addRow("Host:", self.host_label)
            details_layout.addRow("Port:", self.port_label)
            details_layout.addRow("Database:", self.dbname_label)
            details_layout.addRow("Username:", self.user_label)
            details_layout.addRow("Password:", self.password_label)
            connection_layout.addLayout(details_layout)
            
            # Connection actions
            actions_layout = QHBoxLayout()
            self.connect_btn = QPushButton("Connect")
            self.connect_btn.clicked.connect(self.handle_connect)
            self.disconnect_btn = QPushButton("Disconnect")
            self.disconnect_btn.clicked.connect(self.handle_disconnect)
            self.disconnect_btn.setEnabled(False)
            
            for btn in [self.connect_btn, self.disconnect_btn]:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #3d3d3d;
                        padding: 5px 10px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                    }
                    QPushButton:disabled {
                        background-color: #1d1d1d;
                        color: #666666;
                        border: 1px solid #2d2d2d;
                    }
                """)
                actions_layout.addWidget(btn)
            
            actions_layout.addStretch()
            connection_layout.addLayout(actions_layout)
            connection_group.setLayout(connection_layout)
            db_layout.addWidget(connection_group)
            
            # Query section
            query_group = QGroupBox("Query")
            query_group.setStyleSheet("""
                QGroupBox {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    margin-top: 1em;
                    padding: 10px;
                }
                QGroupBox::title {
                    color: #ffffff;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }
            """)
            query_layout = QVBoxLayout()
            
            # Table selection
            table_layout = QHBoxLayout()
            self.table_input = QLineEdit()
            self.table_input.setPlaceholderText("Enter table name...")
            self.table_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    padding: 5px;
                    border-radius: 4px;
                }
                QLineEdit:hover {
                    border: 1px solid #4d4d4d;
                }
            """)
            table_layout.addWidget(QLabel("Table:"))
            table_layout.addWidget(self.table_input)
            
            self.query_btn = QPushButton("Query")
            self.query_btn.clicked.connect(self.handle_query)
            self.query_btn.setEnabled(False)
            self.query_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                }
                QPushButton:disabled {
                    background-color: #1d1d1d;
                    color: #666666;
                    border: 1px solid #2d2d2d;
                }
            """)
            table_layout.addWidget(self.query_btn)
            table_layout.addStretch()
            query_layout.addLayout(table_layout)
            
            # Results table
            self.results_table = QTableWidget()
            self.results_table.setStyleSheet("""
                QTableWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    gridline-color: #3d3d3d;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QHeaderView::section {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #3d3d3d;
                }
            """)
            query_layout.addWidget(self.results_table)
            query_group.setLayout(query_layout)
            db_layout.addWidget(query_group)
            
            # Set up the tab
            db_tab.setLayout(db_layout)
            tab_widget.addTab(db_tab, "Database")
            
            # Initialize the connection combo box
            self.update_connection_combo()
            
            # Connect signals
            self.connection_combo.currentIndexChanged.connect(self.handle_connection_selected)
            
        except Exception as e:
            logger.error(f"Error setting up database tab: {str(e)}")
            raise

    def check_api_health(self):
        """Check the health of all APIs and update the status display"""
        # Clear existing status widgets
        for i in reversed(range(self.api_status_layout.count())): 
            self.api_status_layout.itemAt(i).widget().setParent(None)
        
        # Create status widgets for each API
        for api_url in self.api_endpoints:
            status_widget = QWidget()
            status_layout = QHBoxLayout()
            
            # API name label
            name_label = QLabel(api_url.split('/')[2])
            name_label.setStyleSheet("color: #ffffff;")
            status_layout.addWidget(name_label)
            
            # Status indicator
            status_indicator = QLabel("Checking...")
            status_indicator.setStyleSheet("color: #888888;")
            status_layout.addWidget(status_indicator)
            
            status_widget.setLayout(status_layout)
            self.api_status_layout.addWidget(status_widget)
            
            # Start health check in background
            self.start_api_health_check(api_url, status_indicator)
        
        # Update last checked timestamp
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.last_checked_label.setText(f"Last checked: {current_time}")
        
        # Schedule next check
        QTimer.singleShot(60000, self.check_api_health)  # Check every minute

    def start_api_health_check(self, api_url, status_indicator):
        """Start a health check for a specific API"""
        worker = ApiHealthWorker(api_url)
        thread = QThread()
        worker.moveToThread(thread)
        # Connect signals
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        # Use functools.partial and QueuedConnection to avoid updating deleted widgets
        def safe_update(status, indicator=status_indicator):
            if indicator and hasattr(indicator, 'setText'):
                try:
                    self.update_api_status(indicator, status)
                except RuntimeError:
                    pass  # Widget was deleted
        worker.status_update.connect(safe_update, Qt.QueuedConnection)
        # Track for cleanup
        self.api_health_threads.append(thread)
        self.api_health_workers.append(worker)
        def cleanup():
            if thread in self.api_health_threads:
                self.api_health_threads.remove(thread)
            if worker in self.api_health_workers:
                self.api_health_workers.remove(worker)
        thread.finished.connect(cleanup)
        worker.finished.connect(cleanup)
        thread.start()

    def update_api_status(self, status_indicator, status):
        """Update the status indicator with the API health check result"""
        if status == "up":
            status_indicator.setText("●")
            status_indicator.setStyleSheet("color: #4CAF50; font-size: 16px;")
        else:
            status_indicator.setText("●")
            status_indicator.setStyleSheet("color: #f44336; font-size: 16px;")

    def _show_loading(self, message):
        """Show loading spinner and status message."""
        self.loading_spinner.setText("⌛")  # Simple spinner emoji
        self.loading_spinner.show()
        self.loading_status.setText(message)
        self.loading_status.show()
        self.fetch_logs_btn.setEnabled(False)

    def _hide_loading(self):
        """Hide loading spinner and status message."""
        self.loading_spinner.hide()
        self.loading_status.hide()
        self.fetch_logs_btn.setEnabled(True)

    def append_system_log(self, message: str, level: str = "info") -> None:
        """Append a message to the system log with appropriate formatting.
        
        Args:
            message: The message to append
            level: The log level (info, warning, error, debug)
        """
        try:
            if not hasattr(self, 'system_log_viewer'):
                logger.error("System log viewer not initialized")
                return
                
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            color = {
                "info": "#2ecc71",    # Green
                "warning": "#f1c40f",  # Yellow
                "error": "#e74c3c",    # Red
                "debug": "#3498db"     # Blue
            }.get(level, "#2ecc71")
            
            formatted_message = f'<span style="color: {color}">[{timestamp}]</span> {message}'
            self.system_log_viewer.append(formatted_message)
            
            # Scroll to bottom
            self.system_log_viewer.verticalScrollBar().setValue(
                self.system_log_viewer.verticalScrollBar().maximum()
            )
            
            # Also log to file
            log_func = getattr(logger, level, logger.info)
            log_func(message)
            
        except Exception as e:
            logger.error(f"Error appending to system log: {str(e)}")

    def append_log_line(self, line: str) -> None:
        """Append a line to the log source viewer.
        
        Args:
            line: The line to append
        """
        try:
            if not hasattr(self, 'log_source_viewer'):
                logger.error("Log source viewer not initialized")
                return
                
            self.log_source_viewer.append(line)
            
            # Scroll to bottom
            self.log_source_viewer.verticalScrollBar().setValue(
                self.log_source_viewer.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            logger.error(f"Error appending to log source: {str(e)}")

    def handle_fetch_azure_logs(self) -> None:
        """Handle fetching logs from the selected web app."""
        selected_webapp = self.webapp_combo.currentText()
        if not selected_webapp:
            self.append_terminal_line("No web app selected", msg_type="error")
            return

        resource_group = self.get_resource_group_for_webapp(selected_webapp)
        if not resource_group:
            self.append_terminal_line(f"Could not determine resource group for {selected_webapp}", msg_type="error")
            return

        self._start_log_streaming(selected_webapp, resource_group)

    def _start_log_streaming(self, webapp_name: str, resource_group: str) -> None:
        """Start streaming logs from the specified web app."""
        try:
            # If already streaming, stop it first
            if hasattr(self, 'log_worker') and self.log_worker:
                self._cleanup_log_thread()

            # Clear only the log source viewer
            self.log_source_viewer.clear()
            
            # Show loading state
            self._show_loading(f"Fetching logs for {webapp_name}...")
            self.fetch_logs_btn.setEnabled(False)
            
            # Create and start log streaming
            from quantumops.azure_webapp import AzureWebApp
            azure_webapp = AzureWebApp(
                tenant_id=self.azure_tenant_id,
                client_id=self.azure_client_id,
                client_secret=self.azure_client_secret
            )
            self.log_worker = LogStreamWorker(azure_webapp, resource_group, webapp_name)
            self.log_worker.log_received.connect(self.append_log_line)
            self.log_worker.error_occurred.connect(self._handle_log_error)
            self.log_worker.finished.connect(self._finish_log_streaming)
            self.log_worker.start()
            
            self.streaming_azure_logs = True
            self.append_terminal_line(f"Started streaming logs for {webapp_name}", msg_type="info")
            
        except Exception as e:
            logger.error(f"Error starting log stream: {str(e)}")
            self.append_terminal_line(f"Error starting log stream: {str(e)}", msg_type="error")
            self._hide_loading()
            self.fetch_logs_btn.setEnabled(True)
            self.streaming_azure_logs = False

    def _handle_log_error(self, error: str) -> None:
        """Handle errors from the log streaming worker."""
        logger.error(f"Log streaming error: {error}")
        self.append_terminal_line(f"Log streaming error: {error}", msg_type="error")
        self._cleanup_log_thread()

    def _finish_log_streaming(self) -> None:
        """Handle completion of log streaming."""
        self.append_terminal_line("Log streaming finished", msg_type="info")
        self._cleanup_log_thread()

    def _show_loading(self, message: str) -> None:
        """Show loading state in the UI.
        
        Args:
            message: The loading message to display
        """
        try:
            if hasattr(self, 'loading_status'):
                self.loading_status.setText(message)
                self.loading_status.setVisible(True)
            if hasattr(self, 'loading_spinner'):
                self.loading_spinner.setVisible(True)
        except Exception as e:
            logger.error(f"Error showing loading state: {str(e)}")

    def _hide_loading(self) -> None:
        """Hide loading state in the UI."""
        try:
            if hasattr(self, 'loading_status'):
                self.loading_status.setVisible(False)
            if hasattr(self, 'loading_spinner'):
                self.loading_spinner.setVisible(False)
        except Exception as e:
            logger.error(f"Error hiding loading state: {str(e)}")

    def _cleanup_log_thread(self):
        """Clean up the log streaming thread."""
        if hasattr(self, 'log_worker') and self.log_worker:
            try:
                self.log_worker.stop()
                self.log_worker.wait()
                self.log_worker.deleteLater()
                self.log_worker = None
            except Exception as e:
                logger.error(f"Error cleaning up log thread: {str(e)}")
            finally:
                self.streaming_azure_logs = False
                self.fetch_logs_btn.setEnabled(True)
                self._hide_loading()

    def refresh_logs(self):
        """Refresh logs if streaming is active."""
        try:
            if hasattr(self, 'log_worker') and self.log_worker:
                # Only refresh if we're actively streaming
                self.log_worker.refresh()
        except Exception as e:
            logger.error(f"Error refreshing logs: {str(e)}")
            self.append_system_log(f"Error refreshing logs: {str(e)}", "error")

    @Slot(str, str)
    def append_terminal_line(self, line: str, msg_type: str = "info"):
        """Append a line to the terminal with color coding based on message type."""
        if not hasattr(self, 'log_window') or not self.log_window:
            return
        from quantumops.logging_utils import append_terminal_line as log_util
        log_util(self.log_window, line, msg_type, log_enabled=True)

    def load_connections(self):
        self.connections = database.load_connections()
        return self.connections

    def save_connections(self):
        database.save_connections(self.connections)

    def handle_connect(self):
        host = self.host_label.text()
        port = self.port_label.text()
        dbname = self.dbname_label.text()
        user = self.user_label.text()
        password = self.connections[self.connection_combo.currentIndex() - 1]['password']
        try:
            self.append_terminal_line(f'Attempting to connect to database...', msg_type="system")
            self.conn = database.connect_to_database(host, port, dbname, user, password)
            self.append_terminal_line(f'Successfully connected to database: {dbname}', msg_type="success")
            self.query_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
            self.connect_btn.setText("Connected!")
            self.connect_btn.setEnabled(False)
            # Automatically run the first fetch after connecting
            self.handle_query()
        except Exception as e:
            self.append_terminal_line(f'Error connecting to database: {str(e)}', msg_type="error")
            self.query_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)

    def handle_disconnect(self):
        if self.conn:
            self.append_terminal_line(f'Attempting to disconnect from database...', msg_type="system")
            database.disconnect_database(self.conn)
            self.conn = None
            self.append_terminal_line('Successfully disconnected from database', msg_type="success")
            self.query_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            self.connect_btn.setText("Connect")
            self.connect_btn.setEnabled(True)

    def handle_query(self):
        if not self.conn:
            self.append_terminal_line('Not connected to database', msg_type="error")
            return
        table_name = self.table_input.text()
        if not table_name:
            self.append_terminal_line('Please enter a table name', msg_type="error")
            return
        try:
            self.append_terminal_line(f'Executing query on table: {table_name}', msg_type="system")
            data = database.query_table(self.conn, table_name)
            # Update the table widget with results
            columns = ["created_at", "type", "message", "details"]
            self.results_table.setColumnCount(len(columns))
            self.results_table.setRowCount(len(data))
            self.results_table.setHorizontalHeaderLabels(columns)
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    if j == 3 and value:
                        # Show plain text, pretty-print JSON if possible
                        try:
                            parsed = json.loads(value)
                            pretty = json.dumps(parsed, indent=2)
                            item = QTableWidgetItem(pretty)
                        except Exception:
                            item = QTableWidgetItem(str(value))
                    else:
                        item = QTableWidgetItem(str(value))
                    self.results_table.setItem(i, j, item)
            self.results_table.resizeColumnsToContents()
            self.results_table.resizeRowsToContents()
            self.append_terminal_line(f'Results displayed in table', msg_type="success")
        except Exception as e:
            self.append_terminal_line(f'Error querying table: {str(e)}', msg_type="error")

    def handle_refresh_builds(self, platform):
        from PySide6.QtWidgets import QPushButton, QTableWidgetItem, QProgressBar, QHeaderView
        from PySide6.QtCore import Qt
        table = self.android_builds_table if platform == "android" else self.ios_builds_table
        try:
            self.append_terminal_line(f"Fetching {platform} builds...", msg_type="system")
            builds_list = builds.fetch_builds(platform)
            table.setRowCount(len(builds_list))
            for i, build in enumerate(builds_list):
                # Populate all columns
                table.setItem(i, 0, QTableWidgetItem(str(build.get('id', ''))))
                table.setItem(i, 1, QTableWidgetItem(str(build.get('status', ''))))
                table.setItem(i, 2, QTableWidgetItem(str(build.get('platform', ''))))
                table.setItem(i, 3, QTableWidgetItem(str(build.get('profile', 'N/A'))))
                table.setItem(i, 4, QTableWidgetItem(str(build.get('app_version', 'N/A'))))
                table.setItem(i, 5, QTableWidgetItem(str(build.get('build_url', ''))))
                # Sanitize error message and set as plain text
                error_msg = html.escape(str(build.get('error', '')))
                error_item = QTableWidgetItem(error_msg)
                table.setItem(i, 6, error_item)
                fingerprint_full = str(build.get('fingerprint', 'fp'))
                fingerprint = fingerprint_full[:7] if len(fingerprint_full) >= 7 else fingerprint_full
                table.setItem(i, 7, QTableWidgetItem(fingerprint))
                table.setItem(i, 8, QTableWidgetItem(str(build.get('build_number', 'N/A'))))
                # Push to Azure button logic: now supports progress bar replacement
                push_btn = QPushButton("Push to Azure")
                def make_push_handler(row, b=build):
                    def handler():
                        progress_bar = QProgressBar()
                        progress_bar.setRange(0, 100)
                        table.setCellWidget(row, 9, progress_bar)
                        self.handle_push_to_azure(b, platform, progress_bar, row)
                    return handler
                push_btn.clicked.connect(make_push_handler(i))
                table.setCellWidget(i, 9, push_btn)
            # Set column resize modes again after populating rows
            header = table.horizontalHeader()
            for col in range(table.columnCount()):
                if col in [0, 5, 6]:
                    header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
                else:
                    header.setSectionResizeMode(col, QHeaderView.Stretch)
            self.append_terminal_line(f"Fetched {len(builds_list)} {platform} builds.", msg_type="success")
            builds.enable_refresh_button(self, platform)
        except Exception as e:
            self.append_terminal_line(f"Error fetching {platform} builds: {e}", msg_type="error")

    def handle_push_to_azure(self, build, platform, progress_bar=None, row=None):
        """
        Downloads the build, saves it with the correct filename pattern, uploads to Azure, and updates the DB.
        Uses pipeline run number from BUILD_ID env var for both filename and DB update if set.
        All UI updates must be done in the main thread (slots/signals).
        """
        from quantumops import builds, database
        import tempfile
        import requests
        import os
        from PySide6.QtCore import QThread
        import logging
        # Log environment variables before upload
        try:
            from main import log_env_vars
            log_env_vars()
        except Exception:
            pass
        build_id_env = os.environ.get('BUILD_ID')
        logging.info(f"[UPLOAD] BUILD_ID = {build_id_env}")
        for k in ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_STORAGE_ACCOUNT", "AZURE_STORAGE_CONTAINER"]:
            logging.info(f"[UPLOAD] {k} = {os.environ.get(k)}")
        table = self.android_builds_table if platform == "android" else self.ios_builds_table
        build_url = build.get('build_url', '')
        # Use pipeline run number for DB update if available
        build_id = os.environ.get('BUILD_ID', str(build.get('id', '')))
        if not build_url:
            self.append_terminal_line("No build URL available for upload.", msg_type="error")
            return
        local_path = None
        temp_dir = None
        try:
            self.append_terminal_line(f"Downloading build {build_id}...", msg_type="system")
            # Save the downloaded file with the correct name in a temp directory
            blob_name = self.build_filename(build, platform)
            temp_dir = tempfile.mkdtemp()
            local_path = os.path.join(temp_dir, os.path.basename(blob_name))
            # Download with progress
            response = requests.get(build_url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_bar and total_size > 0:
                            percent = int((downloaded / total_size) * 50)  # 0-50% for download
                            progress_bar.setValue(percent)
            if not self.validate_filename(blob_name, build, platform):
                self.append_terminal_line(f"Filename validation failed: {blob_name}", msg_type="error")
                if local_path and os.path.exists(local_path):
                    os.remove(local_path)
                if temp_dir and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                if progress_bar and row is not None:
                    # Restore button if validation fails
                    push_btn = QPushButton("Push to Azure")
                    push_btn.clicked.connect(lambda: self.handle_push_to_azure(build, platform, progress_bar, row))
                    table.setCellWidget(row, 9, push_btn)
                return
            # Check required Azure env vars
            required_env = [
                "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
                "AZURE_STORAGE_ACCOUNT", "AZURE_STORAGE_CONTAINER"
            ]
            missing = [var for var in required_env if not os.environ.get(var)]
            if missing:
                self.append_terminal_line(f"Missing Azure environment variables: {', '.join(missing)}", msg_type="error")
                logging.warning(f"[UPLOAD] Missing Azure environment variables: {', '.join(missing)}")
                if local_path and os.path.exists(local_path):
                    os.remove(local_path)
                if temp_dir and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                if progress_bar and row is not None:
                    push_btn = QPushButton("Push to Azure")
                    push_btn.clicked.connect(lambda: self.handle_push_to_azure(build, platform, progress_bar, row))
                    table.setCellWidget(row, 9, push_btn)
                return
            # Start upload in a QThread
            self.append_terminal_line(f"Uploading {blob_name} to Azure...", msg_type="system")
            self.upload_thread = QThread()
            self.upload_worker = UploadWorker(local_path, blob_name)
            self.upload_worker.moveToThread(self.upload_thread)
            self.upload_thread.started.connect(self.upload_worker.run)
            # All UI updates must be done via signals/slots (main thread)
            def upload_progress(percent):
                if progress_bar:
                    progress_bar.setValue(50 + percent // 2)  # 50-100% for upload
            self.upload_worker.progress.connect(upload_progress)
            def on_finished(url, success, error_msg):
                # Only quit the thread, do not call wait() here to avoid deadlocks and thread errors
                self.upload_thread.quit()
                # All UI updates below are safe, as this slot runs in the main thread
                if local_path and os.path.exists(local_path):
                    os.remove(local_path)
                if temp_dir and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                if success:
                    self.append_terminal_line(f"Upload successful! URL: {url}", msg_type="success")
                    # Show modal dialog with download URL
                    self.show_download_url_dialog(url, modal=True)
                    # Update download_url in DB if possible
                    try:
                        if self.conn:
                            table_name = f"{platform}_builds"
                            # Use pipeline run number for DB update if available
                            database.update_download_url(self.conn, table_name, build_id, url)
                            self.append_terminal_line(f"Updated download_url in {table_name} for build {build_id}", msg_type="success")
                    except Exception as db_exc:
                        self.append_terminal_line(f"Failed to update download_url in DB: {db_exc}", msg_type="error")
                else:
                    self.append_terminal_line(f"Upload failed: {error_msg}", msg_type="error")
                if progress_bar and row is not None:
                    # Restore button after completion
                    push_btn = QPushButton("Push to Azure")
                    push_btn.clicked.connect(lambda: self.handle_push_to_azure(build, platform, progress_bar, row))
                    table.setCellWidget(row, 9, push_btn)
                self.status_bar.clearMessage()
            self.upload_worker.finished.connect(on_finished)
            self.upload_thread.start()
        except Exception as e:
            self.append_terminal_line(f"Error uploading build: {e}", msg_type="error")
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
            if temp_dir and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            if progress_bar and row is not None:
                push_btn = QPushButton("Push to Azure")
                push_btn.clicked.connect(lambda: self.handle_push_to_azure(build, platform, progress_bar, row))
                table.setCellWidget(row, 9, push_btn)

    def show_download_url_dialog(self, url: str, modal=False):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QDialogButtonBox, QApplication
        dlg = QDialog(self)
        dlg.setWindowTitle("Build Uploaded Successfully")
        layout = QVBoxLayout()
        label = QLabel("Your build has been uploaded. Download URL:")
        layout.addWidget(label)
        url_edit = QLineEdit(url)
        url_edit.setReadOnly(True)
        layout.addWidget(url_edit)
        copy_btn = QPushButton("Copy to Clipboard")
        def handle_copy():
            QApplication.clipboard().setText(url)
        copy_btn.clicked.connect(handle_copy)
        layout.addWidget(copy_btn)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dlg.accept)
        layout.addWidget(button_box)
        dlg.setLayout(layout)
        if modal:
            dlg.setWindowModality(Qt.ApplicationModal)
        dlg.exec()

    def get_short_profile(self, profile):
        mapping = {'development': 'dev', 'staging': 'stage', 'production': 'prod'}
        return mapping.get(profile, profile)

    def build_filename(self, build, platform):
        """
        Returns the filename in the format:
        {platform}-{environment}-v{version}-{build_id}-{fingerprint}.{ext}
        - platform: 'android' or 'ios'
        - environment: 'dev', 'stage', or 'prod' (from profile)
        - version: app version string
        - build_id: build['appBuildVersion'] (MUST be present)
        - fingerprint: first 7 chars of commit hash
        - ext: .apk for android, .ipa for ios
        Example: android-dev-v1.2.3-123-abcdef1.apk
        """
        platform_folder = f"{platform}-builds"
        profile = self.get_short_profile(str(build.get('profile', 'dev')))
        version = str(build.get('version', build.get('app_version', '0.0.0')))
        build_id = str(build.get('appBuildVersion', None))
        if not build_id:
            raise ValueError("appBuildVersion is required in build dict for filename pattern")
        fingerprint = str(build.get('fingerprint', 'fp'))[:7]
        ext = '.apk' if platform == 'android' else '.ipa'
        filename = f"{platform_folder}/{platform}-{profile}-v{version}-{build_id}-{fingerprint}{ext}"
        return filename

    def validate_filename(self, filename, build, platform):
        """
        Validates that the filename matches the expected pattern using build['appBuildVersion'] as build_id.
        """
        profile = self.get_short_profile(str(build.get('profile', 'dev')))
        version = str(build.get('version', build.get('app_version', '0.0.0')))
        build_id = str(build.get('appBuildVersion', None))
        if not build_id:
            raise ValueError("appBuildVersion is required in build dict for filename validation")
        fingerprint = str(build.get('fingerprint', 'fp'))[:7]
        ext = '.apk' if platform == 'android' else '.ipa'
        expected = f"{platform}-{profile}-v{version}-{build_id}-{fingerprint}{ext}"
        return filename.endswith(expected)

    def handle_add_connection(self):
        dlg = ConnectionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            new_conn = dlg.get_connection()
            self.connections.append(new_conn)
            self.save_connections()
            self.update_connection_combo()
            self.append_terminal_line("Added new connection.", msg_type="success")

    def handle_edit_connection(self):
        idx = self.connection_combo.currentIndex() - 1
        if idx < 0 or idx >= len(self.connections):
            QMessageBox.warning(self, "Edit Connection", "Please select a connection to edit.")
            return
        conn = self.connections[idx]
        dlg = ConnectionDialog(self, conn)
        if dlg.exec() == QDialog.Accepted:
            self.connections[idx] = dlg.get_connection()
            self.save_connections()
            self.update_connection_combo()
            self.append_terminal_line("Edited connection.", msg_type="success")

    def handle_delete_connection(self):
        idx = self.connection_combo.currentIndex() - 1
        if idx < 0 or idx >= len(self.connections):
            QMessageBox.warning(self, "Delete Connection", "Please select a connection to delete.")
            return
        conn_name = self.connections[idx].get('name', 'Unnamed')
        reply = QMessageBox.question(self, "Delete Connection", f"Delete connection '{conn_name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.connections[idx]
            self.save_connections()
            self.update_connection_combo()
            self.append_terminal_line(f"Deleted connection '{conn_name}'.", msg_type="success")

    def update_connection_combo(self):
        self.connection_combo.clear()
        self.connection_combo.addItem("Select connection...")
        for conn in self.connections:
            self.connection_combo.addItem(conn.get('name', ''))

    def handle_connection_selected(self, index):
        # Prevent recursive triggers or invalid index
        if not hasattr(self, '_handling_connection_change'):
            self._handling_connection_change = False
        if self._handling_connection_change:
            return
        self._handling_connection_change = True
        try:
            if index <= 0 or index > len(self.connections):
                # Clear fields if no valid connection is selected
                self.host_label.clear()
                self.port_label.clear()
                self.dbname_label.clear()
                self.user_label.clear()
                # Disconnect if connected
                if self.conn:
                    self.handle_disconnect()
                self._handling_connection_change = False
                return

            # Populate fields with new preset
            conn = self.connections[index - 1]
            self.host_label.setText(conn.get('host', ''))
            self.port_label.setText(str(conn.get('port', '')))
            self.dbname_label.setText(conn.get('dbname', ''))
            self.user_label.setText(conn.get('user', ''))
            
            # Reset connect button state
            self.connect_btn.setText("Connect")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.query_btn.setEnabled(False)
        finally:
            self._handling_connection_change = False

    def toggle_log_area(self):
        visible = self.toggle_log_action.isChecked()
        self.log_window.setVisible(visible)

    def toggle_autoresize(self):
        enabled = self.toggle_autoresize_action.isChecked()
        settings = QSettings()
        settings.setValue("auto_resize_window", enabled)
        self.append_terminal_line(f"Auto-resize window set to {enabled}", msg_type="system")

    def set_theme(self, mode):
        import qdarktheme
        qdarktheme.setup_theme(mode)
        self.update_all_widget_styles()
        if mode == "light":
            self.log_window.setStyleSheet("color: #222; background: #fff;")
        else:
            self.log_window.setStyleSheet("color: #fff; background: #222;")
        self.append_terminal_line(f"Theme set to {mode}", msg_type="system")

    def set_branding_theme(self, brand):
        from quantumops.theming import apply_branding_theme
        apply_branding_theme(brand)
        self.update_all_widget_styles()
        self.append_terminal_line(f"Branding theme set to {brand}", msg_type="system")

    def update_sas_expiry_label(self):
        # Update the SAS token expiration label
        from PySide6.QtCore import QSettings
        import re, datetime, urllib.parse, os
        settings = QSettings()
        # Try all possible sources for the SAS token
        sas_token = os.environ.get('AZURE_SAS_TOKEN', '')
        if not sas_token:
            sas_token = settings.value('sas_token', '')
        if not sas_token:
            sas_token = settings.value('sas_url', '')
        expiry = None
        if sas_token:
            # Find se=... in the token (works for both URL and query string)
            match = re.search(r'se=([^&]+)', sas_token)
            if match:
                try:
                    expiry_str = urllib.parse.unquote(match.group(1))
                    expiry = datetime.datetime.strptime(expiry_str, "%Y-%m-%dT%H:%M:%SZ")
                except Exception:
                    expiry = match.group(1)
        if expiry and isinstance(expiry, datetime.datetime):
            now = datetime.datetime.utcnow()
            delta = expiry - now
            if delta.total_seconds() < 0:
                color = "red"
                text = "SAS token expired"
            elif delta.total_seconds() < 3600:
                color = "orange"
                text = f"SAS expires in {int(delta.total_seconds() // 60)} min"
            else:
                color = "green"
                text = f"SAS expires in {delta}"
            self.sas_expiry_label.setText(text)
            self.sas_expiry_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        else:
            self.sas_expiry_label.setText("No SAS token")
            self.sas_expiry_label.setStyleSheet("color: gray;")

    def update_sas_token(self):
        # Modal dialog to update SAS token
        from PySide6.QtWidgets import QInputDialog
        settings = QSettings()
        current = settings.value('sas_url', '')
        new_sas, ok = QInputDialog.getText(self, "Update SAS Token", "Enter new SAS token URL:", text=current or "")
        if ok and new_sas:
            settings.setValue('sas_url', new_sas)
            self.append_terminal_line("SAS token updated.", msg_type="success")
            self.update_sas_expiry_label()
        elif ok:
            self.append_terminal_line("SAS token update cancelled or empty.", msg_type="warning")

    def update_button_styles(self, buttons, prominent=False):
        colors = get_current_brand_colors()
        if prominent:
            style = f'''
                QPushButton {{
                    min-width: 180px;
                    min-height: 38px;
                    font-size: 16px;
                    font-weight: bold;
                    background-color: {colors['primary']};
                    color: #fff;
                    border-radius: 6px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {colors['accent']};
                }}
                QPushButton:pressed {{
                    background-color: #00334d;
                }}
            '''
        else:
            style = f'''
                QPushButton {{
                    min-width: 80px;
                    min-height: 28px;
                    font-size: 14px;
                    background-color: {colors['primary']};
                    color: #fff;
                    border-radius: 4px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {colors['accent']};
                }}
                QPushButton:pressed {{
                    background-color: #00334d;
                }}
            '''
        for btn in buttons:
            btn.setStyleSheet(style)

    def update_log_styles(self):
        colors = get_current_brand_colors()
        # Example: update log window background and text color
        self.log_window.setStyleSheet(f"color: #fff; background: #222; border: 1px solid {colors['primary']};")
        # You may want to update log message color mapping as well

    def update_all_widget_styles(self):
        brand_colors = get_current_brand_colors()
        
        # Update button styles
        for btn in [self.add_conn_btn, self.edit_conn_btn, self.del_conn_btn, 
                   self.android_refresh_btn, self.ios_refresh_btn, self.fetch_logs_btn]:
            if btn:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {brand_colors['primary']};
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {brand_colors['accent']};
                    }}
                    QPushButton:pressed {{
                        background-color: {brand_colors['primary']};
                    }}
                """)
        
        # Update log window
        self.update_log_styles()
        
        # Update QComboBox styles
        combo_style = f'''
            QComboBox {{
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid {brand_colors['primary']};
                border-radius: 4px;
                padding: 5px;
                min-width: 6em;
            }}
            QComboBox:hover {{
                border: 1px solid {brand_colors['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
        '''
        self.connection_combo.setStyleSheet(combo_style)
        self.webapp_combo.setStyleSheet(combo_style)
        
        # Update QLineEdit styles
        line_edit_style = f'''
            QLineEdit {{
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid {brand_colors['primary']};
                border-radius: 4px;
                padding: 5px;
            }}
            QLineEdit:hover {{
                border: 1px solid {brand_colors['accent']};
            }}
            QLineEdit:focus {{
                border: 2px solid {brand_colors['accent']};
            }}
        '''
        for widget in self.findChildren(QLineEdit):
            widget.setStyleSheet(line_edit_style)
        
        # Update QTableWidget styles
        table_style = f'''
            QTableWidget {{
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: {brand_colors['primary']};
                border: 1px solid {brand_colors['primary']};
                border-radius: 4px;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {brand_colors['primary']};
                color: #ffffff;
            }}
            QHeaderView::section {{
                background-color: #1e1e1e;
                color: #ffffff;
                padding: 5px;
                border: 1px solid {brand_colors['primary']};
            }}
            QHeaderView::section:hover {{
                background-color: {brand_colors['accent']};
            }}
        '''
        for widget in self.findChildren(QTableWidget):
            widget.setStyleSheet(table_style)
        
        # Update QTextBrowser styles
        text_browser_style = f'''
            QTextBrowser {{
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid {brand_colors['primary']};
                border-radius: 4px;
                padding: 5px;
            }}
        '''
        for widget in self.findChildren(QTextBrowser):
            widget.setStyleSheet(text_browser_style)
        
        # Update QDialog styles
        dialog_style = f'''
            QDialog {{
                background-color: #2b2b2b;
                color: #ffffff;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QDialogButtonBox QPushButton {{
                background-color: {brand_colors['primary']};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                min-width: 80px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {brand_colors['accent']};
            }}
        '''
        for widget in self.findChildren(QDialog):
            widget.setStyleSheet(dialog_style)

    def show_current_token_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QTableWidget, QTableWidgetItem
        import os
        # Get the SAS token
        sas_token = os.environ.get('AZURE_SAS_TOKEN', '')
        if not sas_token:
            from PySide6.QtCore import QSettings
            settings = QSettings()
            sas_token = settings.value('sas_token', '')
        dlg = QDialog(self)
        dlg.setWindowTitle("Current SAS Token")
        layout = QVBoxLayout()
        # Raw token display
        layout.addWidget(QLabel("Raw SAS Token:"))
        token_edit = QTextEdit()
        token_edit.setReadOnly(True)
        token_edit.setPlainText(sas_token)
        layout.addWidget(token_edit)
        # Parse and display breakdown
        layout.addWidget(QLabel("Token Breakdown:"))
        table = QTableWidget()
        pairs = [kv.split('=', 1) for kv in sas_token.split('&') if '=' in kv]
        table.setRowCount(len(pairs))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Key", "Value"])
        for i, (k, v) in enumerate(pairs):
            table.setItem(i, 0, QTableWidgetItem(k))
            table.setItem(i, 1, QTableWidgetItem(v))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dlg.accept)
        layout.addWidget(button_box)
        dlg.setLayout(layout)
        dlg.exec()

    def show_sp_info_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QTableWidget, QTableWidgetItem
        import os
        dlg = QDialog(self)
        dlg.setWindowTitle("Service Principal Info")
        layout = QVBoxLayout()
        # Display SP and storage info
        layout.addWidget(QLabel("Service Principal & Storage Configuration:"))
        table = QTableWidget()
        keys = [
            ("AZURE_CLIENT_ID", os.environ.get("AZURE_CLIENT_ID", "Not set")),
            ("AZURE_TENANT_ID", os.environ.get("AZURE_TENANT_ID", "Not set")),
            ("AZURE_STORAGE_ACCOUNT", os.environ.get("AZURE_STORAGE_ACCOUNT", "Not set")),
            ("AZURE_STORAGE_CONTAINER", os.environ.get("AZURE_STORAGE_CONTAINER", "Not set")),
        ]
        table.setRowCount(len(keys))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Key", "Value"])
        for i, (k, v) in enumerate(keys):
            table.setItem(i, 0, QTableWidgetItem(k))
            table.setItem(i, 1, QTableWidgetItem(v))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dlg.accept)
        layout.addWidget(button_box)
        dlg.setLayout(layout)
        # Auto-size dialog to fit content
        dlg.adjustSize()
        dlg.setMinimumWidth(table.horizontalHeader().length() + 60)
        dlg.setMaximumWidth(table.horizontalHeader().length() + 120)
        dlg.exec()

    def show_about_dialog(self):
        about_text = """
        <h2>QuantumOps</h2>
        <p>DevOps Error Browser & Build Manager</p>
        <p>Version 1.0.0</p>
        <br>
        <p>Developed by:</p>
        <p>Michael Mueller - RosieVision.ai</p>
        <p>Claude - ProjectFlow.ai</p>
        <br>
        <p>Supported by:</p>
        <div style='text-align: center;'>
            <img src=':/images/projectflow_logo.png' width='200' height='50'><br>
            <img src=':/images/rosievision_logo.png' width='200' height='50'>
        </div>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("About QuantumOps")
        msg.setText(about_text)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
        """)
        msg.exec()

    def setup_log_viewers(self):
        # Create a splitter for the log viewers
        log_splitter = QSplitter(Qt.Vertical)
        
        # Log Source Log Window (top)
        log_source_group = QGroupBox("Log Source")
        log_source_layout = QVBoxLayout()
        self.log_source_viewer = QTextEdit()
        self.log_source_viewer.setReadOnly(True)
        self.log_source_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 8px;
            }
        """)
        log_source_layout.addWidget(self.log_source_viewer)
        log_source_group.setLayout(log_source_layout)
        
        # System Log Window (bottom)
        system_log_group = QGroupBox("System Log")
        system_log_layout = QVBoxLayout()
        self.system_log_viewer = QTextEdit()
        self.system_log_viewer.setReadOnly(True)
        self.system_log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 8px;
            }
        """)
        system_log_layout.addWidget(self.system_log_viewer)
        system_log_group.setLayout(system_log_layout)
        
        # Add both log viewers to the splitter
        log_splitter.addWidget(log_source_group)
        log_splitter.addWidget(system_log_group)
        
        # Set initial sizes (60% for log source, 40% for system log)
        log_splitter.setSizes([600, 400])
        
        # Set the splitter as the central widget
        self.setCentralWidget(log_splitter)

    def update_resource_group_combo(self):
        """This method is no longer needed as we use predefined web apps."""
        pass

    def handle_resource_group_selected(self):
        """This method is no longer needed as we use predefined web apps."""
        pass

    def update_webapp_combo(self):
        """This method is no longer needed as we use predefined web apps."""
        pass

    # --- Builds logic: to be modularized into quantumops/builds.py ---
    # --- Theming logic: to be modularized into quantumops/theming.py ---
    # --- Settings logic: to be modularized into quantumops/settings.py ---
    # --- Logging helpers: to be modularized into quantumops/logging_utils.py ---
    # ... rest of the original methods ... 

    # Remove or stub load_settings
    def load_settings(self):
        pass 

    def get_resource_group_for_webapp(self, webapp_name: str) -> str:
        """Get the resource group name for a given web app."""
        if webapp_name.startswith("RV-"):
            if "Dev" in webapp_name:
                return "RosieVision-Dev"
            else:
                return "RosieVision-Staging"
        elif webapp_name.startswith("PF-"):
            if "Dev" in webapp_name:
                return "Projectflow-Dev"
            else:
                return "ProjectFlow-Staging"
        return ""