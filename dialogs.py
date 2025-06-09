"""
Dialog windows for the PostgreSQL Error Browser.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox
)

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection Settings")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.host_input = QLineEdit()
        self.port_input = QLineEdit("5432")
        self.dbname_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Port:", self.port_input)
        form_layout.addRow("Database:", self.dbname_input)
        form_layout.addRow("User:", self.user_input)
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def set_connection(self, connection):
        """Set the dialog fields from a connection dictionary"""
        self.name_input.setText(connection.get('name', ''))
        self.host_input.setText(connection.get('host', ''))
        self.port_input.setText(str(connection.get('port', '5432')))
        self.dbname_input.setText(connection.get('dbname', ''))
        self.user_input.setText(connection.get('user', ''))
        self.password_input.setText(connection.get('password', ''))
        
    def get_connection(self):
        """Get the connection details from the dialog fields"""
        name = self.name_input.text().strip()
        host = self.host_input.text().strip()
        port = self.port_input.text().strip()
        dbname = self.dbname_input.text().strip()
        user = self.user_input.text().strip()
        password = self.password_input.text()
        
        if not all([name, host, port, dbname, user]):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please fill in all required fields."
            )
            return None
            
        try:
            port = int(port)
        except ValueError:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Port must be a number."
            )
            return None
            
        return {
            'name': name,
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        } 