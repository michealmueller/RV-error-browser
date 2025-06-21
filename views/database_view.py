"""
Database view for connection form and query interface.
"""
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class DatabaseView(QWidget):
    """View for database operations."""

    # Signals
    connect_requested = Signal(str, int, str, str, str)  # host, port, db, user, pass
    query_requested = Signal(str)  # query string
    disconnect_requested = Signal()

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Connection form
        form_layout = QFormLayout()

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost")
        form_layout.addRow("Host:", self.host_input)

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(5432)
        form_layout.addRow("Port:", self.port_input)

        self.database_input = QLineEdit()
        form_layout.addRow("Database:", self.database_input)

        self.user_input = QLineEdit()
        form_layout.addRow("Username:", self.user_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)

        # Connection buttons
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._on_connect)
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self._on_disconnect)
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)

        # Status label
        self.status_label = QLabel("Not connected")
        self.status_label.setStyleSheet("color: red;")

        # Query interface
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your SQL query here...")
        self.query_input.setText("SELECT * FROM error_logs")
        self.query_input.setMaximumHeight(100)

        self.execute_button = QPushButton("Execute Query")
        self.execute_button.clicked.connect(self._on_execute)
        self.execute_button.setEnabled(False)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)

        # Add all components to main layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("Query:"))
        layout.addWidget(self.query_input)
        layout.addWidget(self.execute_button)
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.results_table)

    def _on_connect(self):
        """Handle connect button click."""
        host = self.host_input.text()
        port = self.port_input.value()
        database = self.database_input.text()
        user = self.user_input.text()
        password = self.password_input.text()

        if not all([host, database, user, password]):
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        self.connect_requested.emit(host, port, database, user, password)

    def _on_disconnect(self):
        """Handle disconnect button click."""
        self.disconnect_requested.emit()

    def _on_execute(self):
        """Handle execute query button click."""
        query = self.query_input.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Error", "Please enter a query")
            return
        self.query_requested.emit(query)

    def update_connection_status(self, connected: bool, message: str):
        """Update connection status display."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: green;" if connected else "color: red;")
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
        self.execute_button.setEnabled(connected)

    def display_results(self, results: List[dict]):
        """Display query results in the table."""
        if not results:
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            return

        # Set up table
        self.results_table.setRowCount(len(results))
        self.results_table.setColumnCount(len(results[0]))

        # Set headers
        headers = list(results[0].keys())
        self.results_table.setHorizontalHeaderLabels(headers)

        # Fill data
        for row, result in enumerate(results):
            for col, value in enumerate(result.values()):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.results_table.setItem(row, col, item)

        # Resize columns to content
        self.results_table.resizeColumnsToContents()

    def closeEvent(self, event):
        """Handle window close event."""
        self.disconnect_requested.emit()
        super().closeEvent(event)

    def show_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "Error", message)
