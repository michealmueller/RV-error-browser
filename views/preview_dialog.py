"""
Dialog for previewing build details.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox
)

class PreviewDialog(QDialog):
    """Dialog for previewing build details."""
    
    def __init__(self, build_id: str, platform: str, version: str, parent=None):
        """Initialize preview dialog."""
        super().__init__(parent)
        self.build_id = build_id
        self.platform = platform
        self.version = version
        self.share_url = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle(f"Build Preview - {self.build_id}")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Build info table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Add build info
        info = [
            ("Build ID", self.build_id),
            ("Platform", self.platform),
            ("Version", self.version),
            ("Status", "Available"),
            ("Size", "1.2 GB"),  # This should come from actual build data
            ("Created", "2024-03-20 10:00:00"),  # This should come from actual build data
            ("Branch", "main"),  # This should come from actual build data
            ("Commit", "abc123"),  # This should come from actual build data
        ]
        
        self.table.setRowCount(len(info))
        for row, (key, value) in enumerate(info):
            self.table.setItem(row, 0, QTableWidgetItem(key))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))
            
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self.install_build)
        button_layout.addWidget(self.install_button)
        
        self.share_button = QPushButton("Share")
        self.share_button.clicked.connect(self.share_build)
        button_layout.addWidget(self.share_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def install_build(self):
        """Install the build."""
        try:
            # Installation logic here
            QMessageBox.information(
                self,
                "Installation Started",
                f"Installing build {self.build_id}..."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"Failed to install build: {str(e)}"
            )
            
    def share_build(self):
        """Share the build."""
        try:
            # Share logic here
            self.share_url = f"https://example.com/builds/{self.build_id}"
            QMessageBox.information(
                self,
                "Share URL",
                f"Share URL copied to clipboard: {self.share_url}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Share Failed",
                f"Failed to share build: {str(e)}"
            ) 