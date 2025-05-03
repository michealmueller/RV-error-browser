"""
Main application window and logic for the database viewer.
"""

import sys
import logging
from datetime import datetime
import psycopg2
from psycopg2 import Error
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QTableWidget,
    QTableWidgetItem, QFormLayout, QComboBox, QMessageBox,
    QSplitter, QDialog, QMenuBar, QMenu, QDialogButtonBox, QTextEdit
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction

from delegates import DetailsDelegate, format_details
from dialogs import ConnectionDialog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conn = None
        self.connections = self.load_connections()
        self.setup_ui()
        
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
        """Setup the main window and UI components"""
        self.setWindowTitle("PostgreSQL Viewer")
        self.setMinimumSize(800, 600)
        
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
        self.connection_combo.setMinimumWidth(200)  # Make combo box wider
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
            
    def handle_connect(self):
        """Handle database connection"""
        host = self.host_input.text()
        port = self.port_input.text()
        dbname = self.dbname_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        
        try:
            self.log_message(f'Attempting to connect to database...', "INFO")
            self.log_message(f'Connection details:', "INFO")
            self.log_message(f'  Host: {host}:{port}', "INFO")
            self.log_message(f'  Database: {dbname}', "INFO")
            self.log_message(f'  User: {user}', "INFO")
            
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password
            )
            self.log_message(f'Successfully connected to database: {dbname}', "SUCCESS")
            self.log_message(f'Connection established at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "INFO")
            self.query_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
            self.connect_btn.setText("Connected!")
            self.connect_btn.setEnabled(False)
        except Error as e:
            self.log_message(f'Error connecting to database: {str(e)}', "ERROR")
            self.log_message(f'Connection attempt failed at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "ERROR")
            self.query_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            
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
            
    def handle_query(self):
        """Handle table query"""
        if not self.conn:
            self.log_message('Not connected to database', "ERROR")
            return
            
        table_name = self.table_input.text()
        try:
            self.log_message(f'Executing query on table: {table_name}', "INFO")
            self.log_message(f'Query: SELECT type, message, details FROM public.{table_name}', "INFO")
            
            cursor = self.conn.cursor()
            cursor.execute(f'SELECT type, message, details FROM public.{table_name}')
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            
            self.log_message(f'Query executed successfully', "SUCCESS")
            self.log_message(f'Retrieved {len(data)} rows', "INFO")
            self.log_message(f'Columns: {", ".join(columns)}', "INFO")
            
            # Update table widget
            self.results_table.setColumnCount(len(columns))
            self.results_table.setRowCount(len(data))
            self.results_table.setHorizontalHeaderLabels(columns)
            
            # Set custom delegate for details column
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
                    
            # Adjust column widths
            self.results_table.resizeColumnsToContents()
            self.results_table.resizeRowsToContents()
            
            self.log_message(f'Results displayed in table', "SUCCESS")
            
        except Error as e:
            self.log_message(f'Error querying table: {str(e)}', "ERROR")
            self.log_message(f'Query failed at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "ERROR")
            
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
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        clear_action = QAction("Clear Log", self)
        clear_action.triggered.connect(self.handle_clear_all)
        view_menu.addAction(clear_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_about(self):
        QMessageBox.about(self, "About PostgreSQL Viewer",
                         "PostgreSQL Viewer v1.0\n\n"
                         "A tool for browsing PostgreSQL error logs.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec()) 