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
    QFrame, QTabWidget, QSizePolicy, QProgressBar, QFileDialog, QTreeWidget, QTreeWidgetItem, QStyle
)
from PySide6.QtCore import Qt, QSettings, QTimer
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
from quantumops import database
from quantumops import builds
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log_enabled = False
        self.conn = None
        self.connections = database.load_connections()
        self.eas_setup_complete = False
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("QuantumOps")
        self.resize(1000, 700)
        # Menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        # File menu
        file_menu = self.menu_bar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setStatusTip("Exit the application")
        file_menu.addAction(exit_action)
        # View menu
        view_menu = self.menu_bar.addMenu("View")
        self.toggle_log_action = QAction("Show Log Area", self, checkable=True)
        self.toggle_log_action.setChecked(True)
        self.toggle_log_action.setStatusTip("Show or hide the log/terminal area")
        self.toggle_log_action.triggered.connect(self.toggle_log_area)
        view_menu.addAction(self.toggle_log_action)
        self.toggle_autoresize_action = QAction("Auto-Resize Window on Table Overflow", self, checkable=True)
        self.toggle_autoresize_action.setChecked(True)
        self.toggle_autoresize_action.setStatusTip("Enable or disable auto-resize of window when table overflows")
        self.toggle_autoresize_action.triggered.connect(self.toggle_autoresize)
        view_menu.addAction(self.toggle_autoresize_action)
        # Theme menu
        theme_menu = self.menu_bar.addMenu("Theme")
        light_theme_action = QAction("Light", self)
        light_theme_action.setStatusTip("Switch to light theme")
        light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme_action)
        dark_theme_action = QAction("Dark", self)
        dark_theme_action.setStatusTip("Switch to dark theme")
        dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        theme_menu.addSeparator()
        # Branding themes
        for brand in ["Quantum Blue", "Vivid Purple", "Electric Green", "Cyber Pink"]:
            brand_action = QAction(brand, self)
            brand_action.setStatusTip(f"Switch to {brand} branding theme")
            brand_action.triggered.connect(lambda checked, b=brand: self.set_branding_theme(b))
            theme_menu.addAction(brand_action)
        # Settings menu
        settings_menu = self.menu_bar.addMenu("Settings")
        update_sas_action = QAction("Update SAS Token", self)
        update_sas_action.setStatusTip("Update the Azure SAS token")
        update_sas_action.triggered.connect(self.update_sas_token)
        settings_menu.addAction(update_sas_action)
        # Help menu
        help_menu = self.menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.setStatusTip("About QuantumOps")
        about_action.triggered.connect(lambda: QMessageBox.about(self, "About QuantumOps", "QuantumOps - DevOps Error Browser & Build Manager"))
        help_menu.addAction(about_action)
        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        # Tabs
        self.tabs = QTabWidget()
        self.error_browser_tab = QWidget()
        self.android_builds_tab = QWidget()
        self.ios_builds_tab = QWidget()
        self.logs_tab = QWidget()
        self.setup_error_browser_tab()
        self.setup_builds_tab(self.android_builds_tab, "android")
        self.setup_builds_tab(self.ios_builds_tab, "ios")
        self.setup_logs_tab()
        self.tabs.addTab(self.error_browser_tab, "Error Browser")
        self.tabs.addTab(self.android_builds_tab, "Android Builds")
        self.tabs.addTab(self.ios_builds_tab, "iOS Builds")
        self.tabs.addTab(self.logs_tab, "Logs")
        main_layout.addWidget(self.tabs)
        # Log/terminal area
        self.log_window = QTextBrowser()
        self.log_window.setFixedHeight(120)
        main_layout.addWidget(self.log_window)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_error_browser_tab(self):
        layout = QVBoxLayout()
        # Connection controls
        conn_layout = QHBoxLayout()
        self.connection_combo = QComboBox()
        self.connection_combo.addItem("Select connection...")
        for conn in self.connections:
            self.connection_combo.addItem(conn.get('name', ''))
        self.add_conn_btn = QPushButton("Add")
        self.edit_conn_btn = QPushButton("Edit")
        self.del_conn_btn = QPushButton("Delete")
        # Moderate accent style for buttons
        accent = "#005f7f"
        btn_style = f'''
            QPushButton {{
                min-width: 80px;
                min-height: 28px;
                font-size: 14px;
                background-color: {accent};
                color: #fff;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #0077b3;
            }}
            QPushButton:pressed {{
                background-color: #00334d;
            }}
        '''
        for btn in [self.add_conn_btn, self.edit_conn_btn, self.del_conn_btn]:
            btn.setStyleSheet(btn_style)
        conn_layout.addWidget(QLabel("Connection:"))
        conn_layout.addWidget(self.connection_combo)
        conn_layout.addWidget(self.add_conn_btn)
        conn_layout.addWidget(self.edit_conn_btn)
        conn_layout.addWidget(self.del_conn_btn)
        layout.addLayout(conn_layout)
        # DB info fields
        form_layout = QFormLayout()
        self.host_label = QLineEdit()
        self.host_label.setReadOnly(True)
        self.port_label = QLineEdit()
        self.port_label.setReadOnly(True)
        self.dbname_label = QLineEdit()
        self.dbname_label.setReadOnly(True)
        self.user_label = QLineEdit()
        self.user_label.setReadOnly(True)
        # Remove password field
        form_layout.addRow("Host:", self.host_label)
        form_layout.addRow("Port:", self.port_label)
        form_layout.addRow("DB Name:", self.dbname_label)
        form_layout.addRow("User:", self.user_label)
        layout.addLayout(form_layout)
        # Table name and query controls (move table field up)
        table_layout = QHBoxLayout()
        self.table_input = QLineEdit()
        self.table_input.setPlaceholderText("Enter table name...")
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.query_btn = QPushButton("Get Logs")
        table_layout.addWidget(QLabel("Table:"))
        table_layout.addWidget(self.table_input)
        table_layout.addWidget(self.connect_btn)
        table_layout.addWidget(self.disconnect_btn)
        table_layout.addWidget(self.query_btn)
        layout.addLayout(table_layout)
        # Results table
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        self.error_browser_tab.setLayout(layout)
        # Wire up signals
        self.connect_btn.clicked.connect(self.handle_connect)
        self.disconnect_btn.clicked.connect(self.handle_disconnect)
        self.query_btn.clicked.connect(self.handle_query)
        self.add_conn_btn.clicked.connect(self.handle_add_connection)
        self.edit_conn_btn.clicked.connect(self.handle_edit_connection)
        self.del_conn_btn.clicked.connect(self.handle_delete_connection)
        self.connection_combo.currentIndexChanged.connect(self.handle_connection_selected)

    def setup_builds_tab(self, tab_widget, platform):
        layout = QVBoxLayout()
        refresh_btn = QPushButton(f"Refresh {platform.capitalize()} Builds")
        builds_table = QTableWidget()
        builds_table.setColumnCount(6)
        builds_table.setHorizontalHeaderLabels([
            "ID", "Status", "Platform", "Download URL", "Error", "Push to Azure"
        ])
        layout.addWidget(refresh_btn)
        layout.addWidget(builds_table)
        tab_widget.setLayout(layout)
        # Store references for later use
        if platform == "android":
            self.android_builds_table = builds_table
            self.android_refresh_btn = refresh_btn
            self.android_refresh_btn.clicked.connect(lambda: self.handle_refresh_builds("android"))
        else:
            self.ios_builds_table = builds_table
            self.ios_refresh_btn = refresh_btn
            self.ios_refresh_btn.clicked.connect(lambda: self.handle_refresh_builds("ios"))
        # TODO: Implement handle_refresh_builds and Azure upload action

    def setup_logs_tab(self):
        layout = QVBoxLayout()
        self.log_viewer = QTextBrowser()
        layout.addWidget(self.log_viewer)
        self.logs_tab.setLayout(layout)
        # Timer to refresh log viewer
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.refresh_log_viewer)
        self.log_timer.start(2000)  # Refresh every 2 seconds

    def refresh_log_viewer(self):
        try:
            with open('quantumops.log', 'r', encoding='utf-8') as f:
                log_content = f.read()
            self.log_viewer.setPlainText(log_content)
            self.log_viewer.moveCursor(QTextCursor.End)
        except Exception as e:
            self.log_viewer.setPlainText(f"Could not read log file: {e}")

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
            columns = ["type", "message", "details"]
            self.results_table.setColumnCount(len(columns))
            self.results_table.setRowCount(len(data))
            self.results_table.setHorizontalHeaderLabels(columns)
            self.results_table.setItemDelegateForColumn(2, DetailsDelegate())
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    if j == 2 and value:
                        formatted_details = format_details(value)
                        item = QTableWidgetItem()
                        item.setData(Qt.DisplayRole, formatted_details)
                    else:
                        item = QTableWidgetItem(str(value))
                    self.results_table.setItem(i, j, item)
            self.results_table.resizeColumnsToContents()
            self.results_table.resizeRowsToContents()
            self.append_terminal_line(f'Results displayed in table', msg_type="success")
        except Exception as e:
            self.append_terminal_line(f'Error querying table: {str(e)}', msg_type="error")

    def handle_refresh_builds(self, platform):
        from PySide6.QtWidgets import QPushButton
        table = self.android_builds_table if platform == "android" else self.ios_builds_table
        try:
            self.append_terminal_line(f"Fetching {platform} builds...", msg_type="system")
            builds_list = builds.fetch_builds(platform)
            table.setRowCount(len(builds_list))
            for i, build in enumerate(builds_list):
                table.setItem(i, 0, QTableWidgetItem(str(build.get('id', ''))))
                table.setItem(i, 1, QTableWidgetItem(str(build.get('status', ''))))
                table.setItem(i, 2, QTableWidgetItem(str(build.get('platform', ''))))
                table.setItem(i, 3, QTableWidgetItem(str(build.get('artifacts', {}).get('buildUrl', ''))))
                table.setItem(i, 4, QTableWidgetItem(str(build.get('error', ''))))
                push_btn = QPushButton("Push")
                push_btn.setEnabled(bool(build.get('artifacts', {}).get('buildUrl', '')))
                push_btn.clicked.connect(lambda _, b=build, p=platform: self.handle_push_to_azure(b, p, i))
                table.setCellWidget(i, 5, push_btn)
            table.resizeColumnsToContents()
            table.resizeRowsToContents()
            self.append_terminal_line(f"Fetched {len(builds_list)} {platform} builds.", msg_type="success")
        except Exception as e:
            self.append_terminal_line(f"Error fetching {platform} builds: {str(e)}", msg_type="error")

    def handle_push_to_azure(self, build, platform, row):
        from quantumops import builds
        import tempfile
        import requests
        import os
        table = self.android_builds_table if platform == "android" else self.ios_builds_table
        build_url = build.get('artifacts', {}).get('buildUrl', '')
        if not build_url:
            self.append_terminal_line("No build URL available for upload.", msg_type="error")
            return
        try:
            self.append_terminal_line(f"Downloading build {build.get('id', '')}...", msg_type="system")
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                response = requests.get(build_url, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            self.append_terminal_line(f"Downloaded to {tmp_file_path}. Preparing Azure upload...", msg_type="system")
            # Build blob name with platform-specific folder
            profile = build.get('profile', 'default')
            version = build.get('appVersion', 'v0')
            build_id = build.get('id', 'unknown')
            fingerprint = build.get('artifacts', {}).get('buildFingerprint', 'fp')
            ext = '.apk' if platform == 'android' else '.ipa'
            platform_folder = 'android-builds' if platform == 'android' else 'ios-builds'
            blob_name = f"{platform_folder}/{platform}-{profile}-{version}-{build_id}-{fingerprint}{ext}"
            storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT', '')
            container = os.environ.get('AZURE_STORAGE_CONTAINER', '')
            sas_token = os.environ.get('AZURE_SAS_TOKEN_URL', '')
            if not (storage_account and container and sas_token):
                self.append_terminal_line("Missing Azure storage configuration in environment.", msg_type="error")
                os.remove(tmp_file_path)
                return
            blob_url = f"https://{storage_account}.blob.core.windows.net/{container}/{blob_name}"
            self.append_terminal_line(f"Uploading to Azure Blob: {blob_url}", msg_type="system")
            builds.upload_build_to_azure(tmp_file_path, blob_url, sas_token)
            self.append_terminal_line(f"Uploaded build {build.get('id', '')} to Azure.", msg_type="success")
            table.setItem(row, 5, QTableWidgetItem("Uploaded"))
            os.remove(tmp_file_path)
        except Exception as e:
            self.append_terminal_line(f"Error uploading build: {str(e)}", msg_type="error")
            table.setItem(row, 5, QTableWidgetItem("Error"))
            try:
                if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
            except Exception:
                pass

    def append_terminal_line(self, line, msg_type="info"):
        # Simple log window appender
        if hasattr(self, 'log_window') and self.log_window:
            from quantumops.logging_utils import append_terminal_line as log_util
            log_util(self.log_window, line, msg_type, log_enabled=True)
        else:
            print(f"{msg_type.upper()}: {line}")

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
        if index <= 0 or index > len(self.connections):
            # Clear fields if no valid connection is selected
            self.host_label.clear()
            self.port_label.clear()
            self.dbname_label.clear()
            self.user_label.clear()
            return
        conn = self.connections[index - 1]
        self.host_label.setText(conn.get('host', ''))
        self.port_label.setText(str(conn.get('port', '')))
        self.dbname_label.setText(conn.get('dbname', ''))
        self.user_label.setText(conn.get('user', ''))

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
        self.append_terminal_line(f"Theme set to {mode}", msg_type="system")

    def set_branding_theme(self, brand):
        from quantumops.theming import apply_branding_theme
        apply_branding_theme(brand)
        self.append_terminal_line(f"Branding theme set to {brand}", msg_type="system")

    def update_sas_token(self):
        # Modal dialog to update SAS token
        from PySide6.QtWidgets import QInputDialog
        settings = QSettings()
        current = settings.value('sas_url', '')
        new_sas, ok = QInputDialog.getText(self, "Update SAS Token", "Enter new SAS token URL:", text=current or "")
        if ok and new_sas:
            settings.setValue('sas_url', new_sas)
            self.append_terminal_line("SAS token updated.", msg_type="success")
        elif ok:
            self.append_terminal_line("SAS token update cancelled or empty.", msg_type="warning")

    # --- Builds logic: to be modularized into quantumops/builds.py ---
    # --- Theming logic: to be modularized into quantumops/theming.py ---
    # --- Settings logic: to be modularized into quantumops/settings.py ---
    # --- Logging helpers: to be modularized into quantumops/logging_utils.py ---
    # ... rest of the original methods ... 