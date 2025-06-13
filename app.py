"""
Main application window and logic for the database viewer.
"""

import sys
import logging
import requests
from datetime import datetime
import psycopg2
from psycopg2 import Error
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QTableWidget,
    QTableWidgetItem, QFormLayout, QComboBox, QMessageBox,
    QSplitter, QDialog, QMenuBar, QMenu, QDialogButtonBox, QTextEdit,
    QApplication, QStatusBar
)
from PySide6.QtCore import Qt, QSettings, QTimer, QRunnable, Slot, QObject, Signal, QThreadPool
from PySide6.QtGui import QAction, QColor

from delegates import DetailsDelegate, format_details
from dialogs import ConnectionDialog
from theme import ModernTheme

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)

class Worker(QRunnable):
    """
    Worker thread for running functions in the background.
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit((type(e), str(e), e.__traceback__))
        finally:
            self.signals.finished.emit()

class DatabaseApp(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.conn = None
            self.threadpool = QThreadPool()
            self._theme_applied = False
            self.connections = self.load_connections()
            self.health_check_timer = QTimer()
            self.health_check_timer.timeout.connect(self.perform_health_check)
            self.sites = [
                {'name': 'Dev API', 'url': 'https://devapi.rosievision.ai', 'status': 'Unknown'},
                {'name': 'Dev Web', 'url': 'https://dev.rosievision.ai', 'status': 'Unknown'},
                {'name': 'Dev Flow', 'url': 'https://dev.projectflow.ai', 'status': 'Unknown'},
                {'name': 'Dev Flow API', 'url': 'https://devapi.projectflow.ai', 'status': 'Unknown'},
                {'name': 'Stage Flow', 'url': 'https://stage.projectflow.ai', 'status': 'Unknown'},
                {'name': 'Stage Flow API', 'url': 'https://stageapi.projectflow.ai', 'status': 'Unknown'}
            ]
            self.setup_ui()
            logger.info("DatabaseApp initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DatabaseApp: {str(e)}")
            raise
        
    def load_connections(self):
        """Load saved connections from QSettings"""
        settings = QSettings()
        connections = settings.value('connections', [])
        return connections if connections else []
        
    def save_connections(self):
        """Save connections to QSettings"""
        settings = QSettings()
        settings.setValue('connections', self.connections)
        
    def setup_ui(self):
        try:
            self.setWindowTitle("RosieVision Site Health Monitor")
            self.resize(1200, 700)
            self.setMinimumSize(900, 500)

            # Modern stylesheet
            if not self._theme_applied:
                self.setStyleSheet(ModernTheme.get_stylesheet())
                self._theme_applied = True

            # Central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QHBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # Left panel (controls)
            left_panel = QWidget()
            left_panel.setObjectName("card")
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(24, 24, 24, 24)
            left_layout.setSpacing(18)

            # Section header
            connection_label = QLabel("Database Connection")
            connection_label.setObjectName("section-header")
            connection_label.setProperty("class", "section-header")
            left_layout.addWidget(connection_label)

            # Connection controls
            self.connection_combo = QComboBox()
            self.connection_combo.setMinimumWidth(220)
            self.connection_combo.addItem("")
            self.connection_combo.currentIndexChanged.connect(self.connection_changed)
            self.update_connection_combo()

            self.add_connection_btn = QPushButton("Add Connection")
            self.edit_connection_btn = QPushButton("Edit Connection")
            self.delete_connection_btn = QPushButton("Delete Connection")

            connection_btns = QHBoxLayout()
            connection_btns.addWidget(self.add_connection_btn)
            connection_btns.addWidget(self.edit_connection_btn)
            connection_btns.addWidget(self.delete_connection_btn)

            left_layout.addWidget(self.connection_combo)
            left_layout.addLayout(connection_btns)

            # Database form
            form_group = QWidget()
            form_group.setObjectName("card")
            form_layout = QFormLayout(form_group)
            form_layout.setSpacing(14)
            form_layout.setLabelAlignment(Qt.AlignRight)
            form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

            self.host_input = QLineEdit()
            self.port_input = QLineEdit("5432")
            self.dbname_input = QLineEdit()
            self.user_input = QLineEdit()
            self.password_input = QLineEdit()
            self.table_input = QLineEdit("error_logs")
            self.password_input.setEchoMode(QLineEdit.Password)

            self.host_input.setReadOnly(True)
            self.port_input.setReadOnly(True)
            self.dbname_input.setReadOnly(True)
            self.user_input.setReadOnly(True)
            self.password_input.setReadOnly(True)

            form_layout.addRow("Host:", self.host_input)
            form_layout.addRow("Port:", self.port_input)
            form_layout.addRow("Database:", self.dbname_input)
            form_layout.addRow("Username:", self.user_input)
            form_layout.addRow("Password:", self.password_input)
            form_layout.addRow("Table Name:", self.table_input)

            left_layout.addWidget(form_group)

            # Action buttons
            button_group = QWidget()
            button_group.setObjectName("card")
            button_layout = QHBoxLayout(button_group)
            button_layout.setSpacing(12)

            self.connect_btn = QPushButton("Connect")
            self.disconnect_btn = QPushButton("Disconnect")
            self.query_btn = QPushButton("Get Logs")
            self.clear_log_btn = QPushButton("Clear All")

            self.connect_btn.clicked.connect(self.handle_connect)
            self.disconnect_btn.clicked.connect(self.handle_disconnect)
            self.query_btn.clicked.connect(self.handle_query)
            self.clear_log_btn.clicked.connect(self.handle_clear_all)

            self.disconnect_btn.setEnabled(False)
            self.query_btn.setEnabled(False)

            button_layout.addWidget(self.connect_btn)
            button_layout.addWidget(self.disconnect_btn)
            button_layout.addWidget(self.query_btn)
            button_layout.addWidget(self.clear_log_btn)

            left_layout.addWidget(button_group)
            left_layout.addStretch()

            # Right panel (logs/results)
            right_panel = QWidget()
            right_panel.setObjectName("card")
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(24, 24, 24, 24)
            right_layout.setSpacing(18)

            # Site health section
            site_health_label = QLabel("Site Health Status")
            site_health_label.setObjectName("section-header")
            site_health_label.setProperty("class", "section-header")
            right_layout.addWidget(site_health_label)

            site_status_group = QWidget()
            site_status_layout = QHBoxLayout(site_status_group)
            site_status_layout.setSpacing(12)
            self.site_status_labels = {}
            for site in self.sites:
                label = QLabel(f"{site['name']}: {site['status']}")
                label.setMinimumWidth(160)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("border-radius: 8px; padding: 6px 10px; background: #f1f8e9; font-weight: bold; font-size: 15px;")
                self.site_status_labels[site['name']] = label
                site_status_layout.addWidget(label)
            right_layout.addWidget(site_status_group)

            # Log output
            log_label = QLabel("Log Output")
            log_label.setObjectName("section-header")
            log_label.setProperty("class", "section-header")
            right_layout.addWidget(log_label)

            self.log_window = QTextBrowser()
            self.log_window.setOpenExternalLinks(True)
            self.log_window.setReadOnly(True)
            self.log_window.setMinimumHeight(120)
            right_layout.addWidget(self.log_window)

            # Results table
            results_label = QLabel("Query Results")
            results_label.setObjectName("section-header")
            results_label.setProperty("class", "section-header")
            right_layout.addWidget(results_label)

            self.results_table = QTableWidget()
            self.results_table.setMinimumHeight(180)
            right_layout.addWidget(self.results_table)

            # Add panels to main layout
            main_layout.addWidget(left_panel, 0)
            main_layout.addWidget(right_panel, 1)

            # Menu bar
            self.create_menu_bar()

            # Status bar (already set up in __init__)
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)

            # Start health check timer (every 30 seconds)
            self.health_check_timer.start(30000)
            logger.info("UI setup completed successfully")
        except Exception as e:
            logger.error(f"Error in setup_ui: {str(e)}")
            raise
        
    def update_connection_combo(self):
        """Update the connection dropdown with current connections"""
        current_text = self.connection_combo.currentText()
        self.connection_combo.clear()
        self.connection_combo.addItem("")
        for conn in self.connections:
            self.connection_combo.addItem(conn['name'])
        index = self.connection_combo.findText(current_text)
        if index >= 0:
            self.connection_combo.setCurrentIndex(index)
            
    def connection_changed(self, index):
        """Handle connection selection change"""
        if not hasattr(self, 'host_input'):
            return
            
        if index <= 0:
            self.host_input.clear()
            self.port_input.setText("5432")
            self.dbname_input.clear()
            self.user_input.clear()
            self.password_input.clear()
            self.table_input.clear()
        else:
            conn = self.connections[index - 1]
            self.host_input.setText(conn['host'])
            self.port_input.setText(conn['port'])
            self.dbname_input.setText(conn['dbname'])
            self.user_input.setText(conn['user'])
            self.password_input.setText(conn['password'])
            self.table_input.setText(conn['table'])
            
    def handle_add_connection(self):
        """Add a new connection"""
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_conn = dialog.get_connection()
            if new_conn['name']:
                self.connections.append(new_conn)
                self.save_connections()
                self.update_connection_combo()
                self.connection_combo.setCurrentText(new_conn['name'])
                # Force update of connection fields
                self.connection_changed(self.connection_combo.currentIndex())
                
    def handle_edit_connection(self):
        """Edit selected connection"""
        index = self.connection_combo.currentIndex()
        if index > 0:
            dialog = ConnectionDialog(self, self.connections[index - 1])
            if dialog.exec() == QDialog.Accepted:
                new_conn = dialog.get_connection()
                if new_conn['name']:
                    self.connections[index - 1] = new_conn
                    self.save_connections()
                    self.update_connection_combo()
                    self.connection_combo.setCurrentText(new_conn['name'])
                    # Force update of connection fields
                    self.connection_changed(self.connection_combo.currentIndex())
                    
    def handle_delete_connection(self):
        """Delete selected connection"""
        index = self.connection_combo.currentIndex()
        if index > 0:
            reply = QMessageBox.question(
                self, 'Delete Connection',
                'Are you sure you want to delete this connection?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.connections[index - 1]
                self.save_connections()
                self.update_connection_combo()
                self.connection_combo.setCurrentIndex(0)
                
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message to both the UI and the logger"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = {
            "INFO": "black",
            "ERROR": "red",
            "SUCCESS": "green",
            "WARNING": "orange"
        }.get(level, "black")
        
        html_message = f'<div style="color: {color}">[{timestamp}] {message}</div>'
        self.log_window.append(html_message)
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
            
    def execute_in_thread(self, fn, on_result, on_error=None, on_finished=None):
        """Execute a function in a background thread."""
        worker = Worker(fn)
        worker.signals.result.connect(on_result)
        if on_error:
            worker.signals.error.connect(on_error)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        self.threadpool.start(worker)

    def handle_connect(self):
        """Handle database connection in a background thread."""
        self.log_message(f'Attempting to connect to database...', "INFO")
        self.connect_btn.setEnabled(False)

        host = self.host_input.text()
        port = self.port_input.text()
        dbname = self.dbname_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        
        def connect_task():
            return psycopg2.connect(
                host=host, port=port, dbname=dbname, user=user, password=password
            )

        self.execute_in_thread(connect_task, self.on_connection_success, self.on_connection_error)

    def on_connection_success(self, conn):
        """Handle successful database connection."""
        self.conn = conn
        self.log_message(f'Successfully connected to database: {self.dbname_input.text()}', "SUCCESS")
        self.query_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(True)
        self.connect_btn.setText("Connected!")
        self.perform_health_check()

    def on_connection_error(self, error_tuple):
        """Handle database connection error."""
        exctype, value, tb = error_tuple
        self.log_message(f'Error connecting to database: {value}', "ERROR")
        self.connect_btn.setEnabled(True)

    def handle_disconnect(self):
        """Handle database disconnection"""
        if self.conn:
            self.log_message(f'Attempting to disconnect from database...', "INFO")
            self.conn.close()
            self.conn = None
            self.log_message('Successfully disconnected from database', "INFO")
            self.log_message(f'Disconnected at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "INFO")
            self.query_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            self.connect_btn.setText("Connect")
            self.connect_btn.setEnabled(True)
            self.update_site_status(self.sites[0]['name'], self.sites[0]['status'], self.sites[0]['color'])
            
    def handle_query(self):
        """Handle table query"""
        if not self.conn:
            self.log_message('Not connected to database', "ERROR")
            return
            
        table_name = self.table_input.text()
        self.log_message(f'Executing query on table: {table_name}', "INFO")
        self.query_btn.setEnabled(False)

        def query_task():
            cursor = self.conn.cursor()
            cursor.execute(f'SELECT type, message, details FROM public.{table_name}')
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            return columns, data

        self.execute_in_thread(query_task, self.on_query_success, self.on_query_error, lambda: self.query_btn.setEnabled(True))

    def on_query_success(self, result):
        """Handle successful query execution."""
        columns, data = result
        self.log_message(f'Query executed successfully. Retrieved {len(data)} rows', "SUCCESS")

        self.results_table.setColumnCount(len(columns))
        self.results_table.setRowCount(len(data))
        self.results_table.setHorizontalHeaderLabels(columns)
        
        self.results_table.setItemDelegateForColumn(2, DetailsDelegate())
        
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                item_data = format_details(value) if j == 2 and value else str(value)
                item = QTableWidgetItem()
                item.setData(Qt.DisplayRole, item_data)
                self.results_table.setItem(i, j, item)
                
        self.results_table.resizeColumnsToContents()
        self.results_table.resizeRowsToContents()
        self.log_message(f'Results displayed in table', "SUCCESS")

    def on_query_error(self, error_tuple):
        """Handle query error."""
        exctype, value, tb = error_tuple
        self.log_message(f'Error querying table: {value}', "ERROR")

    def handle_clear_all(self):
        """Clear both the log window and results table"""
        if self.conn:
            self.log_message(f'Attempting to disconnect from database...', "INFO")
            self.conn.close()
            self.conn = None
            self.log_message("Successfully disconnected from database", "INFO")
            self.log_message(f'Disconnected at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "INFO")
            self.query_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            self.connect_btn.setText("Connect")
            self.connect_btn.setEnabled(True)
        self.log_message("Clearing all output...", "INFO")
        self.log_window.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.log_message("All output cleared", "INFO")
        
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            self.health_check_timer.stop()
            if self.conn:
                self.conn.close()
            event.accept()
        except Exception as e:
            logger.error(f"Error in closeEvent: {str(e)}")
            event.accept()

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Connection", self)
        new_action.triggered.connect(self.handle_add_connection)
        file_menu.addAction(new_action)
        
        edit_action = QAction("Edit Connection", self)
        edit_action.triggered.connect(self.handle_edit_connection)
        file_menu.addAction(edit_action)
        
        delete_action = QAction("Delete Connection", self)
        delete_action.triggered.connect(self.handle_delete_connection)
        file_menu.addAction(delete_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        clear_action = QAction("Clear Log", self)
        clear_action.triggered.connect(self.handle_clear_all)
        view_menu.addAction(clear_action)
        
        # Add UI mode toggle action
        self.ui_mode_action = QAction("Switch to New UI", self)
        self.ui_mode_action.triggered.connect(self.toggle_ui_mode)
        self.ui_mode_action.setEnabled(False) # Disable for now
        view_menu.addAction(self.ui_mode_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_about(self):
        QMessageBox.about(self, "About PostgreSQL Viewer",
                         "PostgreSQL Viewer v1.0\n\n"
                         "A tool for browsing PostgreSQL error logs.")

    def toggle_ui_mode(self):
        # Toggle between current UI and UI revamp UI
        if self.ui_mode_action.text() == "Switch to New UI":
            self.ui_mode_action.setText("Switch to Current UI")
            self.setup_ui_revamp()
        else:
            self.ui_mode_action.setText("Switch to New UI")
            self.setup_ui_current()

    def setup_ui_revamp(self):
        """Setup the revamped UI with modern split layout"""
        # Clear existing UI
        for widget in self.findChildren(QWidget):
            widget.deleteLater()
            
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)  # Remove spacing between panels
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove outer margins
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create splitter for left and right panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)  # Thin splitter handle
        splitter.setChildrenCollapsible(False)  # Prevent panels from collapsing
        
        # Create left panel with modern styling
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")  # For styling
        left_panel.setStyleSheet("""
            QWidget#leftPanel {
                background-color: #f5f5f5;
                border-right: 1px solid #e0e0e0;
            }
            QLabel {
                color: #424242;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:read-only {
                background-color: #F5F5F5;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)  # Increased spacing between elements
        left_layout.setContentsMargins(16, 16, 16, 16)  # Consistent margins
        
        # Connection management section
        connection_group = QWidget()
        connection_group.setObjectName("connectionGroup")
        connection_group.setStyleSheet("""
            QWidget#connectionGroup {
                background-color: white;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        connection_layout = QVBoxLayout(connection_group)
        connection_layout.setSpacing(12)
        
        # Connection header
        connection_header = QHBoxLayout()
        connection_label = QLabel("Connection")
        connection_label.setStyleSheet("font-size: 14px; color: #424242;")
        connection_header.addWidget(connection_label)
        connection_header.addStretch()
        
        # Connection controls
        connection_controls = QHBoxLayout()
        connection_controls.setSpacing(8)
        
        self.connection_combo = QComboBox()
        self.connection_combo.setMinimumWidth(200)
        self.connection_combo.addItem("")
        self.connection_combo.currentIndexChanged.connect(self.connection_changed)
        self.update_connection_combo()
        
        self.add_connection_btn = QPushButton("Add")
        self.edit_connection_btn = QPushButton("Edit")
        self.delete_connection_btn = QPushButton("Delete")
        
        connection_controls.addWidget(self.connection_combo)
        connection_controls.addWidget(self.add_connection_btn)
        connection_controls.addWidget(self.edit_connection_btn)
        connection_controls.addWidget(self.delete_connection_btn)
        
        connection_layout.addLayout(connection_header)
        connection_layout.addLayout(connection_controls)
        
        # Database connection form
        form_group = QWidget()
        form_group.setObjectName("formGroup")
        form_group.setStyleSheet("""
            QWidget#formGroup {
                background-color: white;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.host_input = QLineEdit()
        self.port_input = QLineEdit("5432")
        self.dbname_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.table_input = QLineEdit("error_logs")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # Make connection fields read-only
        self.host_input.setReadOnly(True)
        self.port_input.setReadOnly(True)
        self.dbname_input.setReadOnly(True)
        self.user_input.setReadOnly(True)
        self.password_input.setReadOnly(True)
        
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Port:", self.port_input)
        form_layout.addRow("Database:", self.dbname_input)
        form_layout.addRow("Username:", self.user_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Table Name:", self.table_input)
        
        # Action buttons
        button_group = QWidget()
        button_group.setObjectName("buttonGroup")
        button_group.setStyleSheet("""
            QWidget#buttonGroup {
                background-color: white;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        button_layout = QHBoxLayout(button_group)
        button_layout.setSpacing(8)
        
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.query_btn = QPushButton("Get Logs")
        self.clear_log_btn = QPushButton("Clear All")
        
        self.connect_btn.clicked.connect(self.handle_connect)
        self.disconnect_btn.clicked.connect(self.handle_disconnect)
        self.query_btn.clicked.connect(self.handle_query)
        self.clear_log_btn.clicked.connect(self.handle_clear_all)
        
        # Initially disable disconnect and query buttons
        self.disconnect_btn.setEnabled(False)
        self.query_btn.setEnabled(False)
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addWidget(self.query_btn)
        button_layout.addWidget(self.clear_log_btn)
        
        # Add all groups to left layout
        left_layout.addWidget(connection_group)
        left_layout.addWidget(form_group)
        left_layout.addWidget(button_group)
        left_layout.addStretch()  # Push everything to the top
        
        # Create right panel
        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_panel.setStyleSheet("""
            QWidget#rightPanel {
                background-color: white;
            }
            QTextBrowser, QTableWidget {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
            QLabel {
                color: #424242;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(16)
        
        # Create vertical splitter for log and results
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setHandleWidth(1)
        right_splitter.setChildrenCollapsible(False)
        
        # Log window container
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(8)
        
        log_header = QHBoxLayout()
        log_label = QLabel("Log Output")
        log_label.setStyleSheet("font-size: 14px; color: #424242;")
        log_header.addWidget(log_label)
        log_header.addStretch()
        
        self.log_window = QTextBrowser()
        self.log_window.setOpenExternalLinks(True)
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        
        log_layout.addLayout(log_header)
        log_layout.addWidget(self.log_window)
        
        # Results container
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(8)
        
        results_header = QHBoxLayout()
        results_label = QLabel("Query Results")
        results_label.setStyleSheet("font-size: 14px; color: #424242;")
        results_header.addWidget(results_label)
        results_header.addStretch()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(0)
        self.results_table.setRowCount(0)
        self.results_table.setShowGrid(False)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setHighlightSections(False)
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E0E0E0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
        """)
        
        results_layout.addLayout(results_header)
        results_layout.addWidget(self.results_table)
        
        # Add containers to right splitter
        right_splitter.addWidget(log_container)
        right_splitter.addWidget(results_container)
        
        # Set initial splitter sizes
        right_splitter.setSizes([200, 400])
        
        # Add right splitter to right panel
        right_layout.addWidget(right_splitter)
        
        # Add panels to main splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)

    def setup_ui_current(self):
        """Setup the current UI with traditional layout"""
        # Clear existing UI
        for widget in self.findChildren(QWidget):
            widget.deleteLater()
            
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create left panel with fixed width
        left_panel = QWidget()
        left_panel.setMaximumWidth(600)
        left_panel.setMinimumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        
        # Connection management
        connection_layout = QHBoxLayout()
        connection_layout.setSpacing(10)
        
        self.connection_combo = QComboBox()
        self.connection_combo.setMinimumWidth(200)
        self.connection_combo.addItem("")
        self.connection_combo.currentIndexChanged.connect(self.connection_changed)
        self.update_connection_combo()
        
        self.add_connection_btn = QPushButton("Add Connection")
        self.edit_connection_btn = QPushButton("Edit Connection")
        self.delete_connection_btn = QPushButton("Delete Connection")
        
        # Set fixed width for buttons
        self.add_connection_btn.setFixedWidth(120)
        self.edit_connection_btn.setFixedWidth(120)
        self.delete_connection_btn.setFixedWidth(120)
        
        self.add_connection_btn.clicked.connect(self.handle_add_connection)
        self.edit_connection_btn.clicked.connect(self.handle_edit_connection)
        self.delete_connection_btn.clicked.connect(self.handle_delete_connection)
        
        connection_layout.addWidget(QLabel("Connection:"))
        connection_layout.addWidget(self.connection_combo)
        connection_layout.addWidget(self.add_connection_btn)
        connection_layout.addWidget(self.edit_connection_btn)
        connection_layout.addWidget(self.delete_connection_btn)
        
        # Database connection form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.host_input = QLineEdit()
        self.port_input = QLineEdit("5432")
        self.dbname_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.table_input = QLineEdit("error_logs")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # Make connection fields read-only
        self.host_input.setReadOnly(True)
        self.port_input.setReadOnly(True)
        self.dbname_input.setReadOnly(True)
        self.user_input.setReadOnly(True)
        self.password_input.setReadOnly(True)
        
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Port:", self.port_input)
        form_layout.addRow("Database:", self.dbname_input)
        form_layout.addRow("Username:", self.user_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Table Name:", self.table_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.query_btn = QPushButton("Get Logs")
        self.clear_log_btn = QPushButton("Clear All")
        
        # Set fixed width for buttons
        self.disconnect_btn.setFixedWidth(100)
        self.query_btn.setFixedWidth(100)
        self.clear_log_btn.setFixedWidth(100)
        
        self.connect_btn.clicked.connect(self.handle_connect)
        self.disconnect_btn.clicked.connect(self.handle_disconnect)
        self.query_btn.clicked.connect(self.handle_query)
        self.clear_log_btn.clicked.connect(self.handle_clear_all)
        
        # Initially disable disconnect and query buttons
        self.disconnect_btn.setEnabled(False)
        self.query_btn.setEnabled(False)
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addWidget(self.query_btn)
        button_layout.addWidget(self.clear_log_btn)
        
        # Create splitter for log and results
        splitter = QSplitter(Qt.Vertical)
        
        # Log window container
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addWidget(QLabel("Log Output:"))
        self.log_window = QTextBrowser()
        self.log_window.setOpenExternalLinks(True)
        self.log_window.setReadOnly(True)
        log_layout.addWidget(self.log_window)
        
        # Add log container to splitter
        splitter.addWidget(log_container)
        
        # Add all widgets to left layout
        left_layout.addLayout(connection_layout)
        left_layout.addLayout(form_layout)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(splitter)
        
        # Create right panel for results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Results container
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.addWidget(QLabel("Query Results:"))
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(0)
        self.results_table.setRowCount(0)
        self.results_table.setShowGrid(False)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setHighlightSections(False)
        results_layout.addWidget(self.results_table)
        
        # Add results container to right panel
        right_layout.addWidget(results_container)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Set stretch factors
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

    def perform_health_check(self):
        """Perform health check on all monitored sites"""
        try:
            for site in self.sites:
                try:
                    # Check site availability
                    response = requests.get(site['url'], timeout=5, verify=False)  # Added verify=False for testing
                    response_time = response.elapsed.total_seconds()
                    
                    if response.status_code == 200:
                        if response_time < 1.0:
                            status = 'OK'
                            color = 'green'
                        elif response_time < 3.0:
                            status = 'Slow'
                            color = 'orange'
                        else:
                            status = 'Very Slow'
                            color = 'red'
                    else:
                        status = f'Error ({response.status_code})'
                        color = 'red'
                        
                    site['status'] = status
                    site['response_time'] = response_time
                    site['last_check'] = datetime.now()
                    
                except requests.RequestException as e:
                    logger.error(f"Error checking {site['name']}: {str(e)}")
                    status = 'Offline'
                    color = 'red'
                    site['status'] = status
                    site['error'] = str(e)
                    site['last_check'] = datetime.now()
                    
                # Update status label
                self.update_site_status(site['name'], status, color)
                
            # Log detailed health information
            self.log_health_details()
            
        except Exception as e:
            logger.error(f"Error in perform_health_check: {str(e)}")
            
    def update_site_status(self, site_name: str, status: str, color: str):
        """Update a site's status label"""
        try:
            label = self.site_status_labels[site_name]
            label.setText(f"{site_name}: {status}")
            label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 0 10px;")
        except Exception as e:
            logger.error(f"Error updating status for {site_name}: {str(e)}")
            
    def log_health_details(self):
        """Log detailed health information for all sites"""
        try:
            self.log_message("Site Health Check Results:", "INFO")
            
            for site in self.sites:
                self.log_message(f"\n{site['name']} Status:", "INFO")
                self.log_message(f"  URL: {site['url']}", "INFO")
                self.log_message(f"  Status: {site['status']}", "INFO")
                
                if 'response_time' in site:
                    self.log_message(f"  Response Time: {site['response_time']:.2f}s", "INFO")
                if 'error' in site:
                    self.log_message(f"  Error: {site['error']}", "ERROR")
                    
                self.log_message(f"  Last Check: {site['last_check'].strftime('%H:%M:%S')}", "INFO")
        except Exception as e:
            logger.error(f"Error in log_health_details: {str(e)}")

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = DatabaseApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1) 