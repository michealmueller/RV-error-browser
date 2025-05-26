"""
Main application window and logic for the database viewer.
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
    QFrame, QTabWidget, QSizePolicy, QProgressBar, QFileDialog, QTreeWidget, QTreeWidgetItem, QStyle
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QPalette, QColor, QFont, QTextCursor, QActionGroup
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODERN_STYLE = """
QMainWindow {
    background-color: #f5f5f5;
}

QLabel {
    color: #2c3e50;
    font-size: 13px;
    font-weight: 500;
}

QComboBox {
    padding: 8px;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    background-color: white;
    min-width: 200px;
}

QComboBox:hover {
    border: 1px solid #3498db;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QLineEdit {
    padding: 8px;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    background-color: white;
}

QLineEdit:focus {
    border: 1px solid #3498db;
}

QPushButton {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    background-color: #3498db;
    color: white;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:disabled {
    background-color: #bdc3c7;
}

QPushButton#connect-btn {
    background-color: #2ecc71;
}

QPushButton#connect-btn:hover {
    background-color: #27ae60;
}

QPushButton#disconnect-btn {
    background-color: #e74c3c;
}

QPushButton#disconnect-btn:hover {
    background-color: #c0392b;
}

QTextBrowser {
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    background-color: white;
    padding: 8px;
    font-family: "Consolas", monospace;
}

QTableWidget {
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    background-color: white;
    gridline-color: #f0f0f0;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #f8f9fa;
    padding: 8px;
    border: none;
    border-right: 1px solid #dcdcdc;
    border-bottom: 1px solid #dcdcdc;
    font-weight: 500;
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dcdcdc;
}

QMenuBar::item {
    padding: 8px 12px;
    color: #2c3e50;
}

QMenuBar::item:selected {
    background-color: #f0f0f0;
}

QMenu {
    background-color: white;
    border: 1px solid #dcdcdc;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
}

QMenu::item:selected {
    background-color: #f0f0f0;
}

QSplitter::handle {
    background-color: #dcdcdc;
    height: 2px;
}

QFrame#connection-info {
    background-color: white;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    padding: 16px;
    margin: 8px 0;
}
"""

class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log_enabled = False  # Ensure this is set before any method uses it
        self.conn = None
        self.connections = self.load_connections()
        self.eas_setup_complete = False
        # Load SAS token from QSettings if present
        settings = QSettings()
        saved_sas = settings.value('sas_url')
        if saved_sas:
            self.sas_url = saved_sas
        else:
            self.sas_url = "https://rosievisionstorage.blob.core.windows.net/mobile-builds?sp=racwl&st=2025-05-25T01:36:44Z&se=2025-05-25T09:36:44Z&spr=https&sv=2024-11-04&sr=c&sig=yictjiL%2FDSYLcsn76HD4AJrrN3fwt6PFyHWmycyZuWk%3D"
        self.sas_expiration_label = QLabel()
        self.set_sas_expiration_label()
        self.current_theme = "light"
        self.current_branding_theme = "Quantum Blue"
        # Set modern style (DISABLED for pyqtdarktheme)
        # self.setStyleSheet(MODERN_STYLE)
        # Set modern font
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        self.setup_ui()
        # Perform EAS setup once on startup
        self.eas_setup_complete = self.ensure_eas_setup()
        qdarktheme.setup_theme(self.current_theme)
        
    def load_connections(self):
        """Load saved connections from QSettings"""
        settings = QSettings()
        connections = settings.value('connections')
        logger.info(f"Loading connections from QSettings: {connections}")
        self.connections = connections if connections else []
        return self.connections
        
    def save_connections(self):
        """Save connections to QSettings"""
        settings = QSettings()
        logger.info(f"Saving connections to QSettings: {self.connections}")
        settings.setValue('connections', self.connections)
        settings.sync()  # Ensure settings are written immediately
        
    def set_sas_expiration_label(self):
        # Parse SAS token for 'se' (expiry)
        parsed = urlparse(self.sas_url)
        qs = parse_qs(parsed.query)
        se = qs.get('se', [None])[0]
        if se:
            try:
                dt = datetime.strptime(se, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                delta = dt - now
                if delta.total_seconds() < 0:
                    # Expired
                    color = "red"
                elif delta <= timedelta(days=3):
                    # 3 days or less
                    color = "#FFD600"  # yellow
                else:
                    color = "#4caf50"  # green
                self.sas_expiration_label.setText(f"SAS Token Expires: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                self.sas_expiration_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            except Exception:
                self.sas_expiration_label.setText(f"SAS Token Expires: {se}")
                self.sas_expiration_label.setStyleSheet("")
        else:
            self.sas_expiration_label.setText("SAS Token Expiration: Unknown")
            self.sas_expiration_label.setStyleSheet("")

    def setup_ui(self):
        """Setup the main window and UI components"""
        self.setWindowTitle("QuantumOps")
        self.setMinimumSize(1024, 768)
        self.create_menu_bar()

        # --- Main content (tabs) ---
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # --- Error Browser Tab (existing UI) ---
        error_browser_tab = QWidget()
        error_browser_layout = QHBoxLayout(error_browser_tab)
        error_browser_layout.setSpacing(16)
        error_browser_layout.setContentsMargins(24, 24, 24, 24)
        
        # Left panel with fixed width
        left_panel = QWidget()
        left_panel.setMaximumWidth(600)
        left_panel.setMinimumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)
        
        # Initialize labels first
        self.host_label = QLabel()
        self.port_label = QLabel("5432")
        self.dbname_label = QLabel()
        self.user_label = QLabel()
        self.password_label = QLabel("********")
        self.table_input = QLineEdit("error_logs")
        
        # Connection management
        connection_layout = QHBoxLayout()
        connection_layout.setSpacing(16)
        
        self.connection_combo = QComboBox()
        self.connection_combo.setMinimumWidth(250)  # Make combo box wider
        self.update_connection_combo()  # This will add the empty item
        # Connect signal after labels are initialized
        self.connection_combo.currentIndexChanged.connect(self.connection_changed)
        
        connection_layout.addWidget(QLabel("Connection:"))
        connection_layout.addWidget(self.connection_combo)
        connection_layout.addStretch()
        
        # Database connection info in a frame
        connection_frame = QFrame()
        connection_frame.setObjectName("connection-info")
        form_layout = QFormLayout(connection_frame)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(16, 16, 16, 16)
        
        form_layout.addRow("Host:", self.host_label)
        form_layout.addRow("Port:", self.port_label)
        form_layout.addRow("Database:", self.dbname_label)
        form_layout.addRow("Username:", self.user_label)
        form_layout.addRow("Password:", self.password_label)
        form_layout.addRow("Table Name:", self.table_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("connect-btn")
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setObjectName("disconnect-btn")
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
        
        # Initially disable buttons
        self.connect_btn.setEnabled(False)  # Disable connect button initially
        self.disconnect_btn.setEnabled(False)
        self.query_btn.setEnabled(False)
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addWidget(self.query_btn)
        button_layout.addWidget(self.clear_log_btn)
        
        # Remove log window container and splitter from left panel
        # (Remove the following lines from setup_ui):
        # splitter = QSplitter(Qt.Vertical)
        # log_container = QWidget()
        # log_layout = QVBoxLayout(log_container)
        # log_header = QLabel("Log Output")
        # self.log_window = QTextBrowser()
        # log_layout.addWidget(log_header)
        # log_layout.addWidget(self.log_window)
        # splitter.addWidget(log_container)
        # left_layout.addWidget(splitter)
        # Instead, just add the connection, connection_frame, button_layout to left_layout:
        left_layout.addLayout(connection_layout)
        left_layout.addWidget(connection_frame)
        left_layout.addLayout(button_layout)
        
        # Create right panel for results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # Results container
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(8)
        
        results_header = QLabel("Query Results")
        results_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 8px;")
        results_layout.addWidget(results_header)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(0)
        self.results_table.setRowCount(0)
        self.results_table.setShowGrid(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setHighlightSections(False)
        self.results_table.setAlternatingRowColors(True)
        results_layout.addWidget(self.results_table)
        
        # Add results container to right panel
        right_layout.addWidget(results_container)
        
        # Add panels to main layout
        error_browser_layout.addWidget(left_panel)
        error_browser_layout.addWidget(right_panel)
        
        # Set stretch factors
        error_browser_layout.setStretch(0, 0)
        error_browser_layout.setStretch(1, 1)
        
        self.tabs.addTab(error_browser_tab, "Error Browser")
        
        # --- Android Builds Tab ---
        self.android_builds_tab = QWidget()
        android_layout = QVBoxLayout(self.android_builds_tab)
        self.android_builds_table = QTableWidget()
        self.android_builds_table.setColumnCount(0)
        self.android_builds_table.setRowCount(0)
        self.android_builds_table.setShowGrid(True)
        self.android_builds_table.verticalHeader().setVisible(False)
        self.android_builds_table.horizontalHeader().setHighlightSections(False)
        self.android_builds_table.setAlternatingRowColors(True)
        android_layout.addWidget(self.android_builds_table)
        self.android_loading = QProgressBar()
        self.android_loading.setVisible(False)
        android_layout.addWidget(self.android_loading)
        self.tabs.addTab(self.android_builds_tab, "Android Builds")
        
        # --- IOS Builds Tab ---
        self.ios_builds_tab = QWidget()
        ios_layout = QVBoxLayout(self.ios_builds_tab)
        self.ios_builds_table = QTableWidget()
        self.ios_builds_table.setColumnCount(0)
        self.ios_builds_table.setRowCount(0)
        self.ios_builds_table.setShowGrid(True)
        self.ios_builds_table.verticalHeader().setVisible(False)
        self.ios_builds_table.horizontalHeader().setHighlightSections(False)
        self.ios_builds_table.setAlternatingRowColors(True)
        ios_layout.addWidget(self.ios_builds_table)
        self.ios_loading = QProgressBar()
        self.ios_loading.setVisible(False)
        ios_layout.addWidget(self.ios_loading)
        self.tabs.addTab(self.ios_builds_tab, "IOS Builds")
        
        # Connect tab change event
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # --- Log/Terminal area ---
        self.log_window = QTextBrowser()
        self.log_window.setOpenExternalLinks(True)
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("background-color: #111; color: #fff; font-family: 'Consolas', monospace; font-size: 13px;")
        self.log_window.setVisible(self.log_enabled)

        # --- Splitter: main content (tabs) + log/terminal ---
        self.main_splitter = QSplitter(Qt.Vertical)
        main_content_widget = QWidget()
        main_content_layout = QVBoxLayout(main_content_widget)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)
        main_content_layout.addWidget(self.tabs)
        self.main_splitter.addWidget(main_content_widget)
        self.main_splitter.addWidget(self.log_window)
        self.main_splitter.setStretchFactor(0, 8)
        self.main_splitter.setStretchFactor(1, 2)
        self.setCentralWidget(self.main_splitter)

        # At the end of setup_ui, add the SAS expiration label to the status bar
        self.statusBar().addPermanentWidget(self.sas_expiration_label)
        
    def update_connection_combo(self):
        """Update the connection dropdown with current connections"""
        current_text = self.connection_combo.currentText()
        logger.info(f"Current combo box text: {current_text}")
        logger.info(f"Current combo box count: {self.connection_combo.count()}")
        logger.info(f"Current connections: {self.connections}")
        
        self.connection_combo.clear()
        self.connection_combo.addItem("")
        for conn in self.connections:
            self.connection_combo.addItem(conn['name'])
        
        index = self.connection_combo.findText(current_text)
        if index >= 0:
            self.connection_combo.setCurrentIndex(index)
        
        logger.info(f"After update - combo box count: {self.connection_combo.count()}")
            
    def connection_changed(self, index):
        """Handle connection selection change"""
        if index <= 0:
            # Reset all fields
            self.host_label.clear()
            self.port_label.setText("5432")
            self.dbname_label.clear()
            self.user_label.clear()
            self.password_label.setText("********")  # Show asterisks for password
            self.table_input.setText("error_logs")  # Set default table name
            # Disable buttons
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            self.query_btn.setEnabled(False)
        else:
            conn = self.connections[index - 1]
            self.host_label.setText(conn['host'])
            self.port_label.setText(conn['port'])
            self.dbname_label.setText(conn['dbname'])
            self.user_label.setText(conn['user'])
            self.password_label.setText("********")  # Show asterisks for password
            self.table_input.setText(conn.get('table', 'error_logs'))  # Use default if not set
            # Enable connect button
            self.connect_btn.setEnabled(True)
            
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
                
    def append_terminal_line(self, line: str, msg_type: str = "info"):
        if not getattr(self, 'log_enabled', True):
            return
        self.log_window.moveCursor(QTextCursor.End)
        color = "#fff"  # default white
        if msg_type == "error":
            color = "#ff5555"  # red
        elif msg_type == "success":
            color = "#50fa7b"  # green
        elif msg_type == "system":
            color = "#bbbbbb"  # grey
        elif msg_type == "info":
            color = "#8be9fd"  # cyan/light blue for info
        self.log_window.append(f'<span style="color:{color};">{line.rstrip()}</span>')
        self.log_window.moveCursor(QTextCursor.End)

    def run_command_and_stream(self, command: list):
        self.append_terminal_line(f"[SYSTEM] Running command: {' '.join(command)}", msg_type="system")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            stdout_line = process.stdout.readline() if process.stdout else ''
            stderr_line = process.stderr.readline() if process.stderr else ''
            if stdout_line:
                self.append_terminal_line(f"[STDOUT] {stdout_line}", msg_type="info")
            if stderr_line:
                self.append_terminal_line(f"[STDERR] {stderr_line}", msg_type="error")
            if not stdout_line and not stderr_line and process.poll() is not None:
                break
        process.wait()
        self.append_terminal_line(f"[SYSTEM] Command finished: {' '.join(command)} (exit {process.returncode})", msg_type="system")
        return process.returncode

    def handle_connect(self):
        """Handle database connection"""
        host = self.host_label.text()
        port = self.port_label.text()
        dbname = self.dbname_label.text()
        user = self.user_label.text()
        password = self.connections[self.connection_combo.currentIndex() - 1]['password']
        
        try:
            self.append_terminal_line(f'Attempting to connect to database...', msg_type="system")
            self.append_terminal_line(f'Connection details:', msg_type="system")
            self.append_terminal_line(f'  Host: {host}:{port}', msg_type="system")
            self.append_terminal_line(f'  Database: {dbname}', msg_type="system")
            self.append_terminal_line(f'  User: {user}', msg_type="system")
            
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password
            )
            self.append_terminal_line(f'Successfully connected to database: {dbname}', msg_type="success")
            self.append_terminal_line(f'Connection established at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', msg_type="system")
            self.query_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
            self.connect_btn.setText("Connected!")
            self.connect_btn.setEnabled(False)
        except Error as e:
            self.append_terminal_line(f'Error connecting to database: {str(e)}', msg_type="error")
            self.append_terminal_line(f'Connection attempt failed at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', msg_type="error")
            self.query_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            
    def handle_disconnect(self):
        """Handle database disconnection"""
        if self.conn:
            self.append_terminal_line(f'Attempting to disconnect from database...', msg_type="system")
            self.conn.close()
            self.conn = None
            self.append_terminal_line('Successfully disconnected from database', msg_type="success")
            self.append_terminal_line(f'Disconnected at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', msg_type="system")
            self.query_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            self.connect_btn.setText("Connect")
            self.connect_btn.setEnabled(True)
            
    def handle_query(self):
        """Handle table query"""
        if not self.conn:
            self.append_terminal_line('Not connected to database', msg_type="error")
            logger.error('Attempted to query without a database connection')
            return
        table_name = self.table_input.text()
        if not table_name:
            self.append_terminal_line('Please enter a table name', msg_type="error")
            logger.error('No table name provided for query')
            return
        try:
            self.append_terminal_line(f'Executing query on table: {table_name}', msg_type="system")
            logger.info(f'Starting query for table: {table_name}')
            self.append_terminal_line(f'Query: SELECT type, message, details FROM public.{table_name}', msg_type="system")
            logger.debug(f'Query: SELECT type, message, details FROM public.{table_name}')
            # Clear existing results
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            logger.debug('Cleared previous results from results_table')
            cursor = self.conn.cursor()
            cursor.execute(f'SELECT type, message, details FROM public.{table_name}')
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            logger.info(f'Fetched {len(data)} rows from table {table_name}')
            self.append_terminal_line(f'Query executed successfully', msg_type="success")
            self.append_terminal_line(f'Retrieved {len(data)} rows', msg_type="system")
            self.append_terminal_line(f'Columns: {", ".join(columns)}', msg_type="system")
            # Update table widget
            self.results_table.setColumnCount(len(columns))
            self.results_table.setRowCount(len(data))
            self.results_table.setHorizontalHeaderLabels(columns)
            logger.debug(f'Set table headers: {columns}')
            # Set custom delegate for details column
            self.results_table.setItemDelegateForColumn(2, DetailsDelegate())
            logger.debug('Set DetailsDelegate for details column')
            for i, row in enumerate(data):
                logger.debug(f'Populating row {i}: {row}')
                for j, value in enumerate(row):
                    if j == 2 and value:
                        formatted_details = format_details(value)
                        item = QTableWidgetItem()
                        item.setData(Qt.DisplayRole, formatted_details)
                    else:
                        item = QTableWidgetItem(str(value))
                    self.results_table.setItem(i, j, item)
            # Adjust column widths
            self.results_table.resizeColumnsToContents()
            self.results_table.resizeRowsToContents()
            logger.info('Results table populated and resized')
            self.append_terminal_line(f'Results displayed in table', msg_type="success")
        except Error as e:
            self.append_terminal_line(f'Error querying table: {str(e)}', msg_type="error")
            self.append_terminal_line(f'Query failed at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', msg_type="error")
            logger.error(f'Error querying table {table_name}: {e}')
            
    def handle_clear_all(self):
        """Clear both the log window and results table"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.query_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            self.connect_btn.setText("Connect")
            self.connect_btn.setEnabled(True)
        self.log_window.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        
    def closeEvent(self, event):
        """Handle window close event"""
        if self.conn:
            self.conn.close()
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
        
        file_menu.addSeparator()  # Add separator between Delete Connection and Set SAS Token
        
        # Set SAS Token action
        set_sas_action = QAction("Set SAS Token...", self)
        set_sas_action.triggered.connect(self.handle_set_sas_token)
        file_menu.addAction(set_sas_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        clear_action = QAction("Clear Log", self)
        clear_action.triggered.connect(self.handle_clear_all)
        view_menu.addAction(clear_action)
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        light_action = QAction("Light", self)
        dark_action = QAction("Dark", self)
        light_action.setCheckable(True)
        dark_action.setCheckable(True)
        theme_group = QActionGroup(self)
        theme_group.addAction(light_action)
        theme_group.addAction(dark_action)
        light_action.setChecked(True)
        theme_menu.addAction(light_action)
        theme_menu.addAction(dark_action)
        light_action.triggered.connect(lambda: self.set_theme("light"))
        dark_action.triggered.connect(lambda: self.set_theme("dark"))
        self.theme_actions = {"light": light_action, "dark": dark_action}

        # Branding Theme submenu
        branding_menu = theme_menu.addMenu("Branding Theme")
        self.branding_themes = {
            "Quantum Blue": {
                "primary": "#00BFFF",
                "info": "#00BFFF",
                "warning": "#FFD600",
                "danger": "#FF5555"
            },
            "Vivid Purple": {
                "primary": "#A259FF",
                "info": "#A259FF",
                "warning": "#FFD600",
                "danger": "#FF5555"
            },
            "Electric Green": {
                "primary": "#00FFB0",
                "info": "#00FFB0",
                "warning": "#FFD600",
                "danger": "#FF5555"
            },
            "Cyber Pink": {
                "primary": "#FF2D95",
                "info": "#FF2D95",
                "warning": "#FFD600",
                "danger": "#FF5555"
            }
        }
        self.branding_theme_actions = {}
        branding_group = QActionGroup(self)
        for theme_name in self.branding_themes:
            action = QAction(theme_name, self)
            action.setCheckable(True)
            branding_group.addAction(action)
            branding_menu.addAction(action)
            action.triggered.connect(lambda checked, t=theme_name: self.set_branding_theme(t))
            self.branding_theme_actions[theme_name] = action
        # Default to Quantum Blue
        self.branding_theme_actions["Quantum Blue"].setChecked(True)
        self.current_branding_theme = "Quantum Blue"

        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_about(self):
        """Show the about dialog."""
        about_text = ("QuantumOps v1.0\n\n"
                     "A modern tool for DevOps, error log browsing, and mobile build management, Through EAS CLI.\n"
                     "© 2025 QuantumOps Team")
        QMessageBox.about(self, "About QuantumOps", about_text)
        self.append_terminal_line("About QuantumOps dialog shown", msg_type="system")

    def on_tab_changed(self, index):
        # Only fetch builds if EAS setup is complete
        if not self.eas_setup_complete:
            return
        if index == 1:
            self.fetch_and_display_builds("android")
        elif index == 2:
            self.fetch_and_display_builds("ios")

    def ensure_eas_setup(self):
        # Check for app.json
        if not os.path.exists("app.json"):
            file, _ = QFileDialog.getOpenFileName(self, "Select app.json", "", "JSON Files (*.json)")
            if file:
                try:
                    shutil.copy(file, "app.json")
                except Exception as e:
                    dlg = QMessageBox(self)
                    dlg.setWindowTitle("File Error")
                    dlg.setIcon(QMessageBox.Critical)
                    dlg.setText("Failed to copy app.json.")
                    dlg.setInformativeText(f"<small>{e}</small>")
                    dlg.exec()
                    return False
            else:
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Missing File")
                dlg.setIcon(QMessageBox.Warning)
                dlg.setText("app.json is required.")
                dlg.setInformativeText("<small>No app.json file was selected.</small>")
                dlg.exec()
                return False
        # Check for eas.json
        if not os.path.exists("eas.json"):
            file, _ = QFileDialog.getOpenFileName(self, "Select eas.json", "", "JSON Files (*.json)")
            if file:
                try:
                    shutil.copy(file, "eas.json")
                except Exception as e:
                    dlg = QMessageBox(self)
                    dlg.setWindowTitle("File Error")
                    dlg.setIcon(QMessageBox.Critical)
                    dlg.setText("Failed to copy eas.json.")
                    dlg.setInformativeText(f"<small>{e}</small>")
                    dlg.exec()
                    return False
            else:
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Missing File")
                dlg.setIcon(QMessageBox.Warning)
                dlg.setText("eas.json is required.")
                dlg.setInformativeText("<small>No eas.json file was selected.</small>")
                dlg.exec()
                return False
        # Run EAS CLI init and stream output
        ret = self.run_command_and_stream([
            "npx", "eas-cli", "init", "--id", "9821d63e-ff8d-4439-b990-9315f9f9463c", "--non-interactive"
        ])
        if ret != 0:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("EAS Init Failed")
            dlg.setIcon(QMessageBox.Critical)
            dlg.setText("EAS CLI initialization failed.")
            dlg.setInformativeText("<small>See terminal output for details.</small>")
            dlg.exec()
            return False
        return True

    def fetch_and_display_builds(self, platform):
        # No need to check setup here, only called if setup is complete
        logger.info(f'Starting fetch_and_display_builds for platform: {platform}')
        if platform == "android":
            table = self.android_builds_table
            loading = self.android_loading
        else:
            table = self.ios_builds_table
            loading = self.ios_loading
        loading.setVisible(True)
        self.append_terminal_line(f"Loading builds for {platform}...", msg_type="system")
        logger.debug(f'Set loading bar visible for {platform}')
        table.setRowCount(0)
        table.setColumnCount(0)
        logger.debug(f'Cleared previous rows and columns in {platform} builds table')
        QApplication.processEvents()
        # Run eas-cli builds:list using npx and stream output
        output_lines = []
        def collect_json(line):
            output_lines.append(line)
        process = subprocess.Popen([
            "yarn", "install"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process = subprocess.Popen([
            "npx", "eas", "build:list", "--platform", platform, "--json", "--non-interactive"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.append_terminal_line(f"$ npx eas build:list --platform {platform} --json --non-interactive", msg_type="system")
        logger.info(f'Running EAS CLI for {platform} builds')
        json_output = ""
        while True:
            stdout_line = process.stdout.readline() if process.stdout else ''
            stderr_line = process.stderr.readline() if process.stderr else ''
            if stdout_line:
                self.append_terminal_line(stdout_line, msg_type="info")
                json_output += stdout_line
            if stderr_line:
                self.append_terminal_line(stderr_line, msg_type="error")
            if not stdout_line and not stderr_line and process.poll() is not None:
                break
        process.wait()
        self.append_terminal_line("Raw JSON output:", msg_type="system")
        self.append_terminal_line(json_output, msg_type="system")
        logger.debug(f'Raw JSON output for {platform}: {json_output[:500]}...')
        match = re.search(r'(\[.*\])', json_output, re.DOTALL)
        if not match:
            table.setRowCount(1)
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Error"])
            table.setItem(0, 0, QTableWidgetItem("Error: Could not extract JSON array from output."))
            self.append_terminal_line("[ERROR] Could not extract JSON array from output.", msg_type="error")
            logger.error(f'Could not extract JSON array from EAS CLI output for {platform}')
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Builds JSON Error")
            dlg.setIcon(QMessageBox.Critical)
            dlg.setText("Could not extract JSON array from EAS CLI output.")
            dlg.setInformativeText(f"<small>Platform: {platform}</small>")
            dlg.exec()
            loading.setVisible(False)
            return
        json_str = match.group(1)
        try:
            builds = json.loads(json_str)
            logger.info(f'Parsed {len(builds)} builds from EAS CLI output for {platform}')
            self.populate_builds_table(builds, platform)
        except Exception as e:
            table.setRowCount(1)
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Error"])
            table.setItem(0, 0, QTableWidgetItem(f"Error: {str(e)}"))
            self.append_terminal_line(f"[ERROR] JSON parsing failed: {e}", msg_type="error")
            logger.error(f'JSON parsing failed for {platform} builds: {e}')
            dlg = QMessageBox(self)
            dlg.setWindowTitle("JSON Parsing Error")
            dlg.setIcon(QMessageBox.Critical)
            dlg.setText("Failed to parse builds JSON output.")
            dlg.setInformativeText(f"<small>{e}</small>")
            dlg.exec()
        loading.setVisible(False)
        logger.info(f'Finished fetch_and_display_builds for {platform}')

    def populate_builds_table(self, builds, platform):
        logger.info(f'Populating builds table for {platform} with {len(builds)} builds')
        table = self.android_builds_table if platform == "android" else self.ios_builds_table
        columns = [
            "Build ID", "Status", "Platform", "Build Profile", "App Version", "Build Version",
            "Commit Hash", "Commit Message", "Initiator", "Channel", "Distribution",
            "Created", "Completed", "Download URL", "Push to Azure", "Error"
        ]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setRowCount(len(builds))
        for row, build in enumerate(builds):
            logger.debug(f'Adding build to table (row {row}): {build}')
            # Extract fields
            build_id = str(build.get("id", ""))
            status = str(build.get("status", ""))
            platform_val = str(build.get("platform", ""))
            build_profile = str(build.get("buildProfile", ""))
            app_version = str(build.get("appVersion", ""))
            build_version = str(build.get("appBuildVersion", ""))
            commit_hash = str(build.get("gitCommitHash", ""))
            commit_msg = str(build.get("gitCommitMessage", ""))
            initiator = str(build.get("initiatingActor", {}).get("displayName", ""))
            channel = str(build.get("channel", ""))
            distribution = str(build.get("distribution", ""))
            created = str(build.get("createdAt", ""))
            completed = str(build.get("completedAt", ""))
            # Download URL
            download_url = None
            artifacts = build.get("artifacts")
            if isinstance(artifacts, dict):
                download_url = artifacts.get("buildUrl")
            # Error message
            error_msg = ""
            if status == "ERRORED" and isinstance(build.get("error"), dict):
                error_msg = build["error"].get("message", "")
                logger.warning(f'Build {build_id} errored: {error_msg}')
            # Set table items
            values = [
                build_id, status, platform_val, build_profile, app_version, build_version,
                commit_hash, commit_msg, initiator, channel, distribution,
                created, completed, download_url if download_url else "N/A", "", error_msg
            ]
            for col, val in enumerate(values):
                if col == 14:
                    continue  # Push to Azure handled below
                table.setItem(row, col, QTableWidgetItem(val))
            # Push to Azure icon
            icon = self.style().standardIcon(QStyle.SP_ArrowUp)
            upload_btn = QPushButton()
            upload_btn.setIcon(icon)
            upload_btn.setFlat(True)
            upload_btn.setToolTip("Upload to Azure")
            if not download_url:
                upload_btn.setEnabled(False)
                upload_btn.setToolTip("No download URL available for this build.")
                logger.info(f'Build {build_id} has no download URL; disabling upload icon')
            else:
                upload_btn.clicked.connect(lambda _, b=build, p=platform, r=row: self.handle_push_to_azure(b, p, r))
            table.setCellWidget(row, 14, upload_btn)
        logger.info(f'Finished populating builds table for {platform}')

        # --- Auto-resize window if horizontal scrollbar is visible ---
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        QApplication.processEvents()
        if table.horizontalScrollBar().isVisible():
            total_width = sum([table.columnWidth(i) for i in range(table.columnCount())])
            vbar_width = table.verticalScrollBar().width() if table.verticalScrollBar().isVisible() else 0
            padding = 80  # extra space for borders/margins
            new_width = total_width + vbar_width + padding
            # Set minimum width to avoid shrinking too much
            min_width = 1024
            new_width = max(new_width, min_width)
            # Set the main window width
            self.resize(new_width, self.height())

    def handle_push_to_azure(self, build, platform, row):
        # 1. Download build to /tmp
        artifacts = build.get("artifacts", {})
        url = artifacts.get("buildUrl")
        if not url:
            self.append_terminal_line("No download URL for this build.", msg_type="error")
            return
        filename = url.split("/")[-1]
        local_path = f"/tmp/{filename}"
        self.append_terminal_line(f"[SYSTEM] Downloading {url} to {local_path}", msg_type="system")
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            self.append_terminal_line(f"[SUCCESS] Downloaded to {local_path}", msg_type="success")
        except Exception as e:
            self.append_terminal_line(f"[ERROR] Download failed: {e}", msg_type="error")
            return
        # 2. Upload to Azure
        folder = "android-builds" if platform == "android" else "ios-builds"
        blob_name = f"{folder}/{filename}"
        blob_url = f"https://rosievisionstorage.blob.core.windows.net/mobile-builds/{blob_name}"
        self.append_terminal_line(f"[SYSTEM] Uploading to Azure: {blob_url}", msg_type="system")
        try:
            blob_client = BlobClient.from_blob_url(f"{blob_url}?{self.sas_url.split('?',1)[1]}")
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            self.append_terminal_line(f"[SUCCESS] Upload complete: {blob_url}", msg_type="success")
        except Exception as e:
            self.append_terminal_line(f"[ERROR] Azure upload failed: {e}", msg_type="error")
            return
        # 3. Validate upload
        try:
            exists = blob_client.exists()
            if exists:
                self.append_terminal_line(f"[SUCCESS] Blob exists in Azure: {blob_url}", msg_type="success")
                # Update button to show Azure path
                table = self.android_builds_table if platform == "android" else self.ios_builds_table
                table.setCellWidget(row, 14, QLabel(f"{blob_url}"))
            else:
                self.append_terminal_line(f"[ERROR] Blob not found after upload!", msg_type="error")
        except Exception as e:
            self.append_terminal_line(f"[ERROR] Validation failed: {e}", msg_type="error")
        # 4. Delete local file
        try:
            os.remove(local_path)
            self.append_terminal_line(f"[SYSTEM] Deleted local file: {local_path}", msg_type="system")
        except Exception as e:
            self.append_terminal_line(f"[ERROR] Failed to delete local file: {e}", msg_type="error")

    def set_branding_theme(self, theme_name):
        self.current_branding_theme = theme_name
        self.apply_current_theme()
        for t, action in self.branding_theme_actions.items():
            action.setChecked(t == theme_name)
        self.reload_window()

    def set_theme(self, theme_name):
        self.current_theme = theme_name
        self.apply_current_theme()
        for t, action in self.theme_actions.items():
            action.setChecked(t == theme_name)
        self.reload_window()

    def apply_current_theme(self):
        # Always use dark for branding themes, but allow light/dark toggle for base
        if self.current_theme == "light":
            DatabaseApp.setup_qdarktheme("light")
        else:
            DatabaseApp.setup_qdarktheme(
                "dark",
                custom_colors=self.branding_themes[self.current_branding_theme]
            )

    @staticmethod
    def setup_qdarktheme(theme_name="light", custom_colors=None):
        # Apply the theme globally to all widgets, with optional custom colors
        if custom_colors:
            qdarktheme.setup_theme(theme=theme_name, custom_colors=custom_colors)
        else:
            qdarktheme.setup_theme(theme=theme_name)

    def reload_window(self):
        # Save geometry and state if desired
        geometry = self.saveGeometry()
        state = self.saveState()
        # Hide and delete current window
        self.hide()
        # Create a new instance and show it
        new_window = DatabaseApp()
        new_window.restoreGeometry(geometry)
        new_window.restoreState(state)
        new_window.show()
        # Close the old window
        self.close()

    def handle_set_sas_token(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Set SAS Token", "Paste new SAS token URL:", text=self.sas_url)
        if ok and text:
            self.sas_url = text
            self.set_sas_expiration_label()
            settings = QSettings()
            settings.setValue('sas_url', self.sas_url)
            settings.sync()

def main():
    import sys
    app = QApplication(sys.argv)
    DatabaseApp.setup_qdarktheme("light")  # Default to light theme
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 