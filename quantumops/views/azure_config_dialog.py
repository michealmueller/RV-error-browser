from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import QSettings
from quantumops.services.azure_service import AzureService

class AzureConfigDialog(QDialog):
    """Dialog for configuring Azure connection settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Azure Configuration")
        self.setup_ui()
        self._load_settings()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Tenant ID
        tenant_layout = QHBoxLayout()
        tenant_layout.addWidget(QLabel("Tenant ID:"))
        self.tenant_id_input = QLineEdit()
        tenant_layout.addWidget(self.tenant_id_input)
        layout.addLayout(tenant_layout)
        
        # Client ID
        client_layout = QHBoxLayout()
        client_layout.addWidget(QLabel("Client ID:"))
        self.client_id_input = QLineEdit()
        client_layout.addWidget(self.client_id_input)
        layout.addLayout(client_layout)
        
        # Client Secret
        secret_layout = QHBoxLayout()
        secret_layout.addWidget(QLabel("Client Secret:"))
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        secret_layout.addWidget(self.client_secret_input)
        layout.addLayout(secret_layout)
        
        # Container
        container_layout = QHBoxLayout()
        container_layout.addWidget(QLabel("Container:"))
        self.container_input = QLineEdit()
        container_layout.addWidget(self.container_input)
        layout.addLayout(container_layout)
        
        # Storage Account
        storage_layout = QHBoxLayout()
        storage_layout.addWidget(QLabel("Storage Account:"))
        self.storage_account_input = QLineEdit()
        storage_layout.addWidget(self.storage_account_input)
        layout.addLayout(storage_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._handle_test_connection)
        button_layout.addWidget(self.test_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._handle_save)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._handle_cancel)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _load_settings(self):
        """Load settings from QSettings."""
        settings = QSettings()
        self.tenant_id_input.setText(settings.value("azure/tenant_id", ""))
        self.client_id_input.setText(settings.value("azure/client_id", ""))
        self.client_secret_input.setText(settings.value("azure/client_secret", ""))
        self.container_input.setText(settings.value("azure/container", ""))
        self.storage_account_input.setText(settings.value("azure/storage_account", ""))
    
    def _save_settings(self):
        """Save settings to QSettings."""
        settings = QSettings()
        settings.setValue("azure/tenant_id", self.tenant_id_input.text())
        settings.setValue("azure/client_id", self.client_id_input.text())
        settings.setValue("azure/client_secret", self.client_secret_input.text())
        settings.setValue("azure/container", self.container_input.text())
        settings.setValue("azure/storage_account", self.storage_account_input.text())
        settings.sync()
    
    def _validate_inputs(self):
        """Validate that all required fields are filled."""
        return all([
            self.tenant_id_input.text(),
            self.client_id_input.text(),
            self.client_secret_input.text(),
            self.container_input.text(),
            self.storage_account_input.text()
        ])
    
    def _handle_save(self):
        """Handle save button click."""
        if not self._validate_inputs():
            QMessageBox.warning(self, "Validation Error", "All fields are required.")
            return
        
        self._save_settings()
        self.accept()
    
    def _handle_cancel(self):
        """Handle cancel button click."""
        self.reject()
    
    def _handle_test_connection(self):
        """Test the Azure connection with current settings."""
        if not self._validate_inputs():
            QMessageBox.warning(self, "Validation Error", "All fields are required.")
            return
        
        try:
            service = AzureService(
                tenant_id=self.tenant_id_input.text(),
                client_id=self.client_id_input.text(),
                client_secret=self.client_secret_input.text(),
                container_name=self.container_input.text(),
                storage_account=self.storage_account_input.text()
            )
            
            if service.initialize():
                QMessageBox.information(self, "Success", "Connection successful!")
            else:
                QMessageBox.critical(self, "Error", "Connection failed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}") 