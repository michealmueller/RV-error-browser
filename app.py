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
    QSplitter, QDialog, QMenuBar, QMenu, QDialogButtonBox, QTextEdit,
    QFrame
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QPalette, QColor, QFont

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
        self.conn = None
        self.connections = self.load_connections()
        
        # Set modern style
        self.setStyleSheet(MODERN_STYLE)
        
        # Set modern font
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        self.setup_ui()
        
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
        
    def setup_ui(self):
        """Setup the main window and UI components"""
        self.setWindowTitle("RVEB - RosieVision Error Browser")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create left panel with fixed width
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
        
        # Create splitter for log and results
        splitter = QSplitter(Qt.Vertical)
        
        # Log window container
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(8)
        
        log_header = QLabel("Log Output")
        log_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 8px;")
        log_layout.addWidget(log_header)
        
        self.log_window = QTextBrowser()
        self.log_window.setOpenExternalLinks(True)
        self.log_window.setReadOnly(True)
        log_layout.addWidget(self.log_window)
        
        # Add log container to splitter
        splitter.addWidget(log_container)
        
        # Add all widgets to left layout
        left_layout.addLayout(connection_layout)
        left_layout.addWidget(connection_frame)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(splitter)
        
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
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Set stretch factors
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)
        
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
                
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message to both the UI and the logger"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = {
            "INFO": "black",
            "ERROR": "red",
            "SUCCESS": "green",
            "WARNING": "orange"
        }.get(level, "black")
        
        html_message = f'<div style="color: {color}">[{timestamp}] [{level}] {message}</div>'
        self.log_window.append(html_message)
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
            
    def handle_connect(self):
        """Handle database connection"""
        host = self.host_label.text()
        port = self.port_label.text()
        dbname = self.dbname_label.text()
        user = self.user_label.text()
        password = self.connections[self.connection_combo.currentIndex() - 1]['password']
        
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
        if not table_name:
            self.log_message('Please enter a table name', "ERROR")
            return
            
        try:
            self.log_message(f'Executing query on table: {table_name}', "INFO")
            self.log_message(f'Query: SELECT type, message, details FROM public.{table_name}', "INFO")
            
            # Clear existing results
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            
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
        """Show the about dialog."""
        about_text = ("RVEB - RosieVision Error Browser v1.0\n\n"
                     "A modern tool for browsing PostgreSQL error logs.\n"
                     "© 2025 RosieVision")
        QMessageBox.about(self, "About RVEB", about_text)
        self.log_message("About RVEB dialog shown", "INFO")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec()) 