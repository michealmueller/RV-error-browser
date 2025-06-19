"""
Dialog for managing health check endpoints.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QMessageBox, QWidget
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)

class HealthSettingsDialog(QDialog):
    """Dialog for managing health check endpoints."""
    
    def __init__(self, health_model, parent=None):
        super().__init__(parent)
        self.health_model = health_model
        self.setWindowTitle("Health Check Settings")
        self.setMinimumSize(600, 400)
        
        # Store temporary webapps dict for editing
        self.webapps = dict(self.health_model.webapps)
        
        self._init_ui()
        self._populate_table()
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Add endpoint section
        add_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Endpoint Name (e.g., MyApp-Dev)")
        add_layout.addWidget(self.name_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Health Check URL (e.g., https://myapp.com/health)")
        add_layout.addWidget(self.url_input)
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_endpoint)
        add_layout.addWidget(add_button)
        
        layout.addLayout(add_layout)
        
        # Endpoints table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "URL", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        
    def _populate_table(self):
        """Populate the table with current endpoints."""
        self.table.setRowCount(0)
        for name, url in self.webapps.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, name_item)
            
            # URL
            url_item = QTableWidgetItem(url)
            self.table.setItem(row, 1, url_item)
            
            # Actions
            actions_widget = self._create_actions_widget(row)
            self.table.setCellWidget(row, 2, actions_widget)
            
        self.table.resizeColumnsToContents()
        
    def _create_actions_widget(self, row):
        """Create actions widget for a table row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self._edit_endpoint(row))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self._delete_endpoint(row))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        layout.addStretch()
        
        return widget
        
    def _add_endpoint(self):
        """Add a new endpoint."""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name or not url:
            QMessageBox.warning(self, "Validation Error", "Both name and URL are required.")
            return
            
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Validation Error", "URL must start with http:// or https://")
            return
            
        self.webapps[name] = url
        self._populate_table()
        
        # Clear inputs
        self.name_input.clear()
        self.url_input.clear()
        
    def _edit_endpoint(self, row):
        """Edit an existing endpoint."""
        name = self.table.item(row, 0).text()
        url = self.table.item(row, 1).text()
        
        # Set values in inputs
        self.name_input.setText(name)
        self.url_input.setText(url)
        
        # Delete old entry
        self._delete_endpoint(row)
        
    def _delete_endpoint(self, row):
        """Delete an endpoint."""
        name = self.table.item(row, 0).text()
        del self.webapps[name]
        self.table.removeRow(row)
        
    def accept(self):
        """Save changes and close dialog."""
        self.health_model.webapps = dict(self.webapps)
        super().accept() 