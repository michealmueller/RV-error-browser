"""
PostgreSQL Error Browser - Main Application Window
"""
import sys
import datetime
import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QSplitter, QTextEdit,
    QMenuBar, QMenu, QStatusBar, QToolBar, QDialog, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QFont

from database import DatabaseManager
from settings import SettingsManager
from theme import ThemeManager
from dialogs import ConnectionDialog

logger = logging.getLogger(__name__)

class DatabaseApp(QMainWindow):
    """Main application window for PostgreSQL Error Browser."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PostgreSQL Error Browser")
        self.setMinimumSize(800, 600)
        
        # Initialize managers
        self.db_manager = DatabaseManager()
        self.settings_manager = SettingsManager()
        self.theme_manager = ThemeManager()
        
        # Set up UI
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # Load saved settings
        self._load_settings()
        
        # Set up auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)
        
    def _setup_ui(self):
        """Set up the main UI components."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for left and right panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Connection management
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Connection form
        form_layout = QFormLayout()
        
        self.connection_combo = QComboBox()
        self.connection_combo.currentIndexChanged.connect(self._on_connection_selected)
        form_layout.addRow("Connection:", self.connection_combo)
        
        self.host_input = QLineEdit()
        form_layout.addRow("Host:", self.host_input)
        
        self.port_input = QLineEdit("5432")
        form_layout.addRow("Port:", self.port_input)
        
        self.database_input = QLineEdit()
        form_layout.addRow("Database:", self.database_input)
        
        self.user_input = QLineEdit()
        form_layout.addRow("User:", self.user_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)
        
        left_layout.addLayout(form_layout)
        
        # Connection buttons
        button_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_database)
        button_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_from_database)
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.disconnect_button)
        
        left_layout.addLayout(button_layout)
        
        # Add connection management buttons
        manage_layout = QHBoxLayout()
        
        self.add_connection_button = QPushButton("Add Connection")
        self.add_connection_button.clicked.connect(self.add_connection)
        manage_layout.addWidget(self.add_connection_button)
        
        self.edit_connection_button = QPushButton("Edit Connection")
        self.edit_connection_button.clicked.connect(self.edit_connection)
        manage_layout.addWidget(self.edit_connection_button)
        
        self.delete_connection_button = QPushButton("Delete Connection")
        self.delete_connection_button.clicked.connect(self.delete_connection)
        manage_layout.addWidget(self.delete_connection_button)
        
        left_layout.addLayout(manage_layout)
        
        # Add stretch to push everything to the top
        left_layout.addStretch()
        
        # Right panel - Log display
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Table for log entries
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Type", "Message", "Details"])
        self.log_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.log_table)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([200, 600])
        
        # Store references
        self.splitter = splitter
        
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self.connect_to_database)
        file_menu.addAction(connect_action)
        
        disconnect_action = QAction("Disconnect", self)
        disconnect_action.triggered.connect(self.disconnect_from_database)
        file_menu.addAction(disconnect_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_logs)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        theme_menu = view_menu.addMenu("Theme")
        for theme_name in self.theme_manager.get_theme_names():
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, t=theme_name: self._change_theme(t))
            theme_menu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self.connect_to_database)
        toolbar.addAction(connect_action)
        
        disconnect_action = QAction("Disconnect", self)
        disconnect_action.triggered.connect(self.disconnect_from_database)
        toolbar.addAction(disconnect_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_logs)
        toolbar.addAction(refresh_action)
        
    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
        
    def _load_settings(self):
        """Load saved settings."""
        # Load saved connections
        connections = self.settings_manager.get_all_connections()
        self.connection_combo.clear()
        for conn in connections:
            self.connection_combo.addItem(conn['name'])
            
        # Load last used connection
        last_connection = self.settings_manager.get_last_connection()
        if last_connection:
            index = self.connection_combo.findText(last_connection)
            if index >= 0:
                self.connection_combo.setCurrentIndex(index)
                
        # Load window geometry
        geometry = self.settings_manager.get_window_geometry()
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))
            
        # Load splitter state
        splitter_state = self.settings_manager.get_splitter_state()
        if splitter_state:
            self.splitter.restoreState(splitter_state)
            
        # Apply theme
        theme = self.settings_manager.get_setting('theme', 'light')
        self._change_theme(theme)
        
        # Set up auto-refresh
        auto_refresh = self.settings_manager.get_setting('auto_refresh', False)
        refresh_interval = self.settings_manager.get_setting('refresh_interval', 30)
        if auto_refresh:
            self.refresh_timer.start(refresh_interval * 1000)
            
    def _save_settings(self):
        """Save current settings."""
        self.settings_manager.set_window_geometry(self.saveGeometry().toHex().data().decode())
        self.settings_manager.set_splitter_state(self.splitter.saveState())
        self.settings_manager.save_settings()
        
    def _change_theme(self, theme_name: str):
        """Change the application theme."""
        self.theme_manager.apply_theme(QApplication.instance(), theme_name)
        self.settings_manager.set_setting('theme', theme_name)
        self.settings_manager.save_settings()
        self.statusbar.showMessage(f"Theme changed to {theme_name}")
        
    def _on_connection_selected(self, index: int):
        """Handle connection selection change."""
        if index < 0:
            return
            
        connection_name = self.connection_combo.currentText()
        connection = self.settings_manager.get_connection(connection_name)
        
        if connection:
            self.host_input.setText(connection.get('host', ''))
            self.port_input.setText(str(connection.get('port', '5432')))
            self.database_input.setText(connection.get('database', ''))
            self.user_input.setText(connection.get('user', ''))
            self.password_input.setText(connection.get('password', ''))
            
    def add_connection(self):
        """Add a new database connection."""
        dialog = ConnectionDialog(self)
        if dialog.exec():
            connection = dialog.get_connection()
            if connection:
                self.settings_manager.add_connection(connection)
                self.settings_manager.save_settings()
                self._load_settings()
                
    def edit_connection(self):
        """Edit the selected database connection."""
        connection_name = self.connection_combo.currentText()
        if not connection_name:
            return
            
        connection = self.settings_manager.get_connection(connection_name)
        if not connection:
            return
            
        dialog = ConnectionDialog(self)
        dialog.set_connection(connection)
        
        if dialog.exec():
            new_connection = dialog.get_connection()
            if new_connection:
                self.settings_manager.add_connection(new_connection)
                self.settings_manager.save_settings()
                self._load_settings()
                
    def delete_connection(self):
        """Delete the selected database connection."""
        connection_name = self.connection_combo.currentText()
        if not connection_name:
            return
            
        reply = QMessageBox.question(
            self,
            "Delete Connection",
            f"Are you sure you want to delete the connection '{connection_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings_manager.remove_connection(connection_name)
            self.settings_manager.save_settings()
            self._load_settings()
            
    def connect_to_database(self):
        """Connect to the selected database."""
        connection_name = self.connection_combo.currentText()
        if not connection_name:
            self.statusbar.showMessage("No connection selected")
            return
            
        connection = self.settings_manager.get_connection(connection_name)
        if not connection:
            self.statusbar.showMessage("Connection not found")
            return
            
        try:
            self.db_manager.connect(
                host=connection['host'],
                port=connection['port'],
                database=connection['database'],
                user=connection['user'],
                password=connection['password']
            )
            
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.statusbar.showMessage(f"Connected to {connection_name}")
            
            # Save last used connection
            self.settings_manager.set_last_connection(connection_name)
            self.settings_manager.save_settings()
            
            # Refresh logs
            self.refresh_logs()
            
        except Exception as e:
            self.statusbar.showMessage(f"Connection failed: {str(e)}")
            QMessageBox.critical(self, "Connection Error", str(e))
            
    def disconnect_from_database(self):
        """Disconnect from the current database."""
        try:
            self.db_manager.disconnect()
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.statusbar.showMessage("Disconnected")
        except Exception as e:
            self.statusbar.showMessage(f"Disconnect failed: {str(e)}")
            QMessageBox.critical(self, "Disconnect Error", str(e))
            
    def refresh_logs(self):
        """Refresh the log display."""
        if not self.db_manager.is_connected():
            return
            
        try:
            logs = self.db_manager.get_logs()
            self.log_table.setRowCount(len(logs))
            
            for i, log in enumerate(logs):
                self.log_table.setItem(i, 0, QTableWidgetItem(log['type']))
                self.log_table.setItem(i, 1, QTableWidgetItem(log['message']))
                self.log_table.setItem(i, 2, QTableWidgetItem(log['details']))
                
            self.statusbar.showMessage(f"Refreshed {len(logs)} logs")
            
        except Exception as e:
            self.statusbar.showMessage(f"Refresh failed: {str(e)}")
            QMessageBox.critical(self, "Refresh Error", str(e))
            
    def log_message(self, message: str, level: str = "info"):
        """Log a message to the status bar."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if level == "error":
            self.statusbar.showMessage(formatted_message, 5000)
            QMessageBox.critical(self, "Error", message)
        elif level == "warning":
            self.statusbar.showMessage(formatted_message, 3000)
            QMessageBox.warning(self, "Warning", message)
        else:
            self.statusbar.showMessage(formatted_message, 2000)
            
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About PostgreSQL Error Browser",
            "PostgreSQL Error Browser\n\n"
            "A tool for browsing and managing PostgreSQL error logs.\n\n"
            "Version 1.0.0"
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        self._save_settings()
        if self.db_manager.is_connected():
            self.db_manager.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec()) 