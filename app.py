"""
Main application window and logic for the database viewer.
"""

import sys
import logging
import requests
from datetime import datetime
import psycopg2
from psycopg2 import Error, sql
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QTableWidget,
    QTableWidgetItem, QFormLayout, QComboBox, QMessageBox,
    QSplitter, QDialog, QMenuBar, QMenu, QDialogButtonBox, QTextEdit,
    QApplication, QStatusBar
)
from PySide6.QtCore import Qt, QSettings, QTimer, QRunnable, Slot, QObject, Signal, QThreadPool
from PySide6.QtGui import QAction, QColor
import os

from delegates import DetailsDelegate, format_details
from dialogs import ConnectionDialog, SiteDialog
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
            self.connections = self.load_connections()
            self.sites = self.load_sites()
            self.health_check_timer = QTimer()
            self.health_check_timer.timeout.connect(self.perform_health_check)
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
        
    def load_sites(self):
        """Load saved sites from QSettings"""
        settings = QSettings()
        sites = settings.value('sites', [])
        return sites if sites else [{'name': 'Default', 'url': 'https://example.com', 'status': 'Unknown'}]

    def save_sites(self):
        """Save sites to QSettings"""
        settings = QSettings()
        settings.setValue('sites', self.sites)
        
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
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)

            # Health status section
            health_group = QWidget()
            health_group.setObjectName("card")
            health_layout = QVBoxLayout(health_group)
            
            health_header_layout = QHBoxLayout()
            site_health_label = QLabel("Site Health Status")
            site_health_label.setObjectName("section-header")
            self.add_site_btn = QPushButton("Add Site")
            self.remove_site_combo = QComboBox()
            self.remove_site_btn = QPushButton("Remove Site")
            health_header_layout.addWidget(site_health_label)
            health_header_layout.addStretch()
            health_header_layout.addWidget(self.add_site_btn)
            health_header_layout.addWidget(self.remove_site_combo)
            health_header_layout.addWidget(self.remove_site_btn)
            
            self.site_status_layout = QHBoxLayout()
            health_layout.addLayout(health_header_layout)
            health_layout.addLayout(self.site_status_layout)
            self.update_site_status_display()

            # DB connection section
            db_group = QWidget()
            db_group.setObjectName("card")
            db_layout = QVBoxLayout(db_group)
            
            connection_label = QLabel("Database Connection")
            connection_label.setObjectName("section-header")
            db_layout.addWidget(connection_label)

            self.connection_combo = QComboBox()
            self.update_connection_combo()

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

            db_layout.addWidget(self.connection_combo)
            db_layout.addWidget(self.host_input)
            db_layout.addWidget(self.port_input)
            db_layout.addWidget(self.dbname_input)
            db_layout.addWidget(self.user_input)
            db_layout.addWidget(self.password_input)
            db_layout.addWidget(self.table_input)

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

            db_layout.addWidget(button_group)

            # Log and results section
            splitter = QSplitter(Qt.Vertical)
            log_widget = QWidget()
            log_layout = QVBoxLayout(log_widget)
            log_layout.addWidget(QLabel("Logs"))
            self.log_window = QTextBrowser()
            log_layout.addWidget(self.log_window)
            
            results_widget = QWidget()
            results_layout = QVBoxLayout(results_widget)
            results_layout.addWidget(QLabel("Results"))
            self.results_table = QTableWidget()
            results_layout.addWidget(self.results_table)

            splitter.addWidget(log_widget)
            splitter.addWidget(results_widget)

            main_layout.addWidget(health_group)
            main_layout.addWidget(db_group)
            main_layout.addWidget(splitter)
            
            # Connect site management buttons
            self.add_site_btn.clicked.connect(self.handle_add_site)
            self.remove_site_btn.clicked.connect(self.handle_remove_site)

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

        # Construct env var name from connection name
        conn_name = self.connection_combo.currentText()
        if not conn_name:
            self.log_message("No connection selected.", "ERROR")
            self.connect_btn.setEnabled(True)
            return

        env_var_name = conn_name.upper().replace('-', '_') + '_DB_PASSWORD'
        password = os.getenv(env_var_name)

        if not password:
            self.log_message(f"Password environment variable not set: {env_var_name}", "ERROR")
            self.connect_btn.setEnabled(True)
            return
        
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
            self.update_site_status_display()
            
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
            query = sql.SQL("SELECT type, message, details FROM public.{}").format(
                sql.Identifier(table_name)
            )
            cursor.execute(query)
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
        self.ui_mode_action.setEnabled(False) 
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
        # This UI is not needed for the core functionality
        pass

    def setup_ui_current(self):
        """Setup the current UI with traditional layout"""
        # This UI is not needed for the core functionality
        pass

    def perform_health_check(self):
        """Perform health check on all monitored sites"""
        for site in self.sites:
            try:
                response = requests.get(site['url'], timeout=5, verify=False)
                if response.status_code == 200:
                    site['status'] = 'OK'
                else:
                    site['status'] = 'Failing'
            except requests.RequestException:
                site['status'] = 'Failing'
            self.update_site_status_display()

    def update_site_status_display(self):
        """Update the site status labels in the UI"""
        for i in reversed(range(self.site_status_layout.count())): 
            self.site_status_layout.itemAt(i).widget().setParent(None)

        self.remove_site_combo.clear()
        for site in self.sites:
            self.remove_site_combo.addItem(site['name'])
            status_label = QLabel(f"{site['name']}: {site['status']}")
            color = "green" if site['status'] == 'OK' else "red"
            status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            self.site_status_layout.addWidget(status_label)

    def handle_add_site(self):
        """Handle adding a new site"""
        dialog = SiteDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_site = dialog.get_site()
            if new_site['name'] and new_site['url']:
                self.sites.append(new_site)
                self.save_sites()
                self.update_site_status_display()

    def handle_remove_site(self):
        """Handle removing a site"""
        site_name_to_remove = self.remove_site_combo.currentText()
        if not site_name_to_remove:
            return

        self.sites = [site for site in self.sites if site['name'] != site_name_to_remove]
        self.save_sites()
        self.update_site_status_display()
            
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = DatabaseApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1) 