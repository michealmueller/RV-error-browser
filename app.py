"""
Main application window for the PostgreSQL Error Browser.
"""
import sys
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

class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PostgreSQL Error Browser")
        self.setMinimumSize(1200, 800)
        
        # Initialize connection
        self.conn = None
        
        # Load saved connections
        self.settings = QSettings("RosieVision", "PostgreSQLViewer")
        self.connections = self.settings.value("connections", [])
        
        # Create main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create left panel with fixed width
        left_panel = QWidget()
        left_panel.setMaximumWidth(600)
        left_layout = QVBoxLayout(left_panel)
        
        # Connection management section
        connection_group = QWidget()
        connection_layout = QVBoxLayout(connection_group)
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
        
        connection_layout.addWidget(QLabel("Saved Connections:"))
        connection_layout.addWidget(self.connection_combo)
        connection_layout.addWidget(self.add_connection_btn)
        connection_layout.addWidget(self.edit_connection_btn)
        connection_layout.addWidget(self.delete_connection_btn)
        
        # Connection details section
        form_group = QWidget()
        form_layout = QFormLayout(form_group)
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
        form_layout.addRow("User:", self.user_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Table:", self.table_input)
        
        # Button section
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)
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
        
        # Add sections to left panel
        left_layout.addWidget(connection_group)
        left_layout.addWidget(form_group)
        left_layout.addWidget(button_group)
        left_layout.addStretch()
        
        # Create right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create splitter for log and results
        splitter = QSplitter(Qt.Vertical)
        
        # Log window
        self.log_window = QTextBrowser()
        self.log_window.setMinimumHeight(200)
        splitter.addWidget(self.log_window)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        splitter.addWidget(self.results_table)
        
        right_layout.addWidget(splitter)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Initial log message
        self.log_message("Application started", "INFO")
        
    def log_message(self, message, level="INFO"):
        """Add a message to the log window with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = {
            "INFO": "black",
            "SUCCESS": "green",
            "ERROR": "red",
            "WARNING": "orange"
        }.get(level, "black")
        
        self.log_window.append(f'<span style="color: {color}">[{timestamp}] {level}: {message}</span>')
        
    def update_connection_combo(self):
        """Update the connection combo box with saved connections"""
        self.connection_combo.clear()
        self.connection_combo.addItem("")
        for conn in self.connections:
            self.connection_combo.addItem(conn['name'])
            
    def save_connections(self):
        """Save connections to settings"""
        self.settings.setValue("connections", self.connections)
        self.settings.sync()
        
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
            return
            
        conn_name = self.connection_combo.currentText()
        for conn in self.connections:
            if conn['name'] == conn_name:
                self.host_input.setText(conn['host'])
                self.port_input.setText(str(conn['port']))
                self.dbname_input.setText(conn['dbname'])
                self.user_input.setText(conn['user'])
                self.password_input.setText(conn['password'])
                break
                
    def handle_add_connection(self):
        """Add a new connection"""
        dialog = ConnectionDialog(self)
        if dialog.exec():
            new_conn = dialog.get_connection()
            if new_conn:
                self.connections.append(new_conn)
                self.save_connections()
                self.update_connection_combo()
                self.connection_combo.setCurrentText(new_conn['name'])
                # Force update of connection fields
                self.connection_changed(self.connection_combo.currentIndex())
                
    def handle_edit_connection(self):
        """Edit selected connection"""
        if self.connection_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Warning", "Please select a connection to edit")
            return
            
        dialog = ConnectionDialog(self)
        dialog.set_connection(self.connections[self.connection_combo.currentIndex() - 1])
        if dialog.exec():
            new_conn = dialog.get_connection()
            if new_conn:
                self.connections[self.connection_combo.currentIndex() - 1] = new_conn
                self.save_connections()
                self.update_connection_combo()
                self.connection_combo.setCurrentText(new_conn['name'])
                # Force update of connection fields
                self.connection_changed(self.connection_combo.currentIndex())
                
    def handle_delete_connection(self):
        """Delete selected connection"""
        if self.connection_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Warning", "Please select a connection to delete")
            return
            
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the connection '{self.connection_combo.currentText()}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.connections[self.connection_combo.currentIndex() - 1]
            self.save_connections()
            self.update_connection_combo()
            
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
            self.log_message("Not connected to database", "ERROR")
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
            
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.results_table.setItem(i, j, item)
                    
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
        """Create the application menu bar"""
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
        """Show the about dialog"""
        QMessageBox.about(self, "About PostgreSQL Viewer",
                         "PostgreSQL Viewer v1.0\n\n"
                         "A tool for browsing PostgreSQL error logs.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec()) 