"""
Dialog windows for the database viewer application.
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt

class ConnectionDialog(QDialog):
    """Dialog for adding/editing database connections"""
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.connection = connection or {}
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Add/Edit Connection")
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit(self.connection.get('name', ''))
        self.host_input = QLineEdit(self.connection.get('host', 'localhost'))
        self.port_input = QLineEdit(self.connection.get('port', '5432'))
        self.dbname_input = QLineEdit(self.connection.get('dbname', ''))
        self.user_input = QLineEdit(self.connection.get('user', ''))
        self.password_input = QLineEdit(self.connection.get('password', ''))
        self.table_input = QLineEdit(self.connection.get('table', ''))
        self.password_input.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Connection Name:", self.name_input)
        layout.addRow("Host:", self.host_input)
        layout.addRow("Port:", self.port_input)
        layout.addRow("Database:", self.dbname_input)
        layout.addRow("Username:", self.user_input)
        layout.addRow("Password:", self.password_input)
        layout.addRow("Default Table:", self.table_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_connection(self):
        return {
            'name': self.name_input.text(),
            'host': self.host_input.text(),
            'port': self.port_input.text(),
            'dbname': self.dbname_input.text(),
            'user': self.user_input.text(),
            'password': self.password_input.text(),
            'table': self.table_input.text()
        }

class SiteDialog(QDialog):
    """Dialog for adding/editing sites for health checks"""
    def __init__(self, parent=None, site=None):
        super().__init__(parent)
        self.site = site or {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Add/Edit Site")
        layout = QFormLayout(self)

        self.name_input = QLineEdit(self.site.get('name', ''))
        self.url_input = QLineEdit(self.site.get('url', ''))

        layout.addRow("Site Name:", self.name_input)
        layout.addRow("URL:", self.url_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_site(self):
        return {
            'name': self.name_input.text(),
            'url': self.url_input.text(),
            'status': 'Unknown'
        } 