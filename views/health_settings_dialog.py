"""
Dialog for managing health check endpoints.
"""
import logging

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.health_check import HealthCheckModel

logger = logging.getLogger(__name__)


class HealthSettingsDialog(QDialog):
    """Dialog for managing health check settings."""

    def __init__(self, model: HealthCheckModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Health Check Settings")
        self.setMinimumSize(600, 400)

        # Main layout
        layout = QVBoxLayout(self)

        # Table for endpoints
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Service Name", "Endpoint URL"])
        layout.addWidget(self.table)

        # Buttons
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_row)
        layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_row)
        layout.addWidget(self.remove_button)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Load current settings
        self._load_settings()

    def _load_settings(self):
        """Load endpoints from the model."""
        endpoints = self.model.webapps
        self.table.setRowCount(len(endpoints))
        for row, (name, url) in enumerate(endpoints.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(url))
        self.table.resizeColumnsToContents()

    def _save_settings(self):
        """Save endpoints to the model and config file."""
        endpoints = {}
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            url_item = self.table.item(row, 1)
            if name_item and url_item:
                endpoints[name_item.text()] = url_item.text()

        self.model.webapps = endpoints
        self.model._save_endpoints(endpoints)
        QMessageBox.information(
            self, "Settings Saved", "Health check endpoints have been updated."
        )

    def _add_row(self):
        """Add a new row to the table."""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

    def _remove_row(self):
        """Remove the selected row from the table."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def accept(self):
        """Handle save action."""
        self._save_settings()
        super().accept()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Add endpoint section
        add_layout = QHBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Endpoint Name (e.g., MyApp-Dev)")
        add_layout.addWidget(self.name_input)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Health Check URL (e.g., https://myapp.com/health)"
        )
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
        self.table.itemChanged.connect(self._on_item_changed)
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

        self.setStyleSheet(
            """
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
        """
        )

    def _populate_table(self):
        """Populate the table with current endpoints."""
        self.table.setRowCount(0)
        self.table.blockSignals(True)  # Block signals during population
        for name, url in self.model.webapps.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Name
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, name_item)

            # URL
            url_item = QTableWidgetItem(url)
            self.table.setItem(row, 1, url_item)

            # Actions
            actions_widget = self._create_actions_widget(row, name)
            self.table.setCellWidget(row, 2, actions_widget)

        self.table.blockSignals(False)  # Unblock signals

        # Auto-resize rows to fit content
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()

        # Set minimum row height to ensure buttons are fully visible
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, max(40, self.table.rowHeight(row)))

    def _create_actions_widget(self, row, name):
        """Create actions widget for a table row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedHeight(28)  # Set fixed height for consistent sizing
        delete_btn.clicked.connect(lambda: self._delete_endpoint(name))
        delete_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """
        )

        layout.addWidget(delete_btn)
        layout.addStretch()

        return widget

    def _add_endpoint(self):
        """Add a new endpoint."""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()

        if not name or not url:
            QMessageBox.warning(
                self, "Validation Error", "Both name and URL are required."
            )
            return

        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(
                self, "Validation Error", "URL must start with http:// or https://"
            )
            return

        self.model.webapps[name] = url
        self._populate_table()

        # Clear inputs
        self.name_input.clear()
        self.url_input.clear()

    def _delete_endpoint(self, name):
        """Delete an endpoint by name."""
        if name in self.model.webapps:
            del self.model.webapps[name]
            self._populate_table()  # Repopulate to reflect change
            logger.info(f"Deleted endpoint: {name}")
        else:
            logger.warning(f"Attempted to delete non-existent endpoint: {name}")

    @Slot(QTableWidgetItem)
    def _on_item_changed(self, item):
        """Handle changes to table items."""
        row = item.row()
        col = item.column()

        # Find the original name from the row before the edit
        # This requires a way to map row to name, as name can be edited.
        # A simple way is to find the key by value, but names must be unique.

        # This is tricky because the key (name) itself can be changed.
        # Let's get the original name before the change.
        # A better approach: use a hidden column or a separate list to store original names.

        # For simplicity, we'll assume names are unique and find the old key.
        # This is brittle. A better implementation would use a model/view architecture.

        # Let's assume the name (column 0) is the key and cannot be edited for simplicity for now.
        # Or, if it is edited, we treat it as a new entry.

        if row >= len(self.model.webapps):
            return  # This is a new row being added, not an edit

        current_name = self.table.item(row, 0).text()
        current_url = self.table.item(row, 1).text()

        # This is still not robust.
        # Let's try a different approach. We find the name from the row, and assume it was the key.

        # We need the key of the item that was at this row.
        # We can store the keys in a list in the same order as the table is populated.

        keys = list(self.model.webapps.keys())
        if row < len(keys):
            old_key = keys[row]

            new_key = self.table.item(row, 0).text()
            new_url = self.table.item(row, 1).text()

            if col == 0:  # Name changed
                if new_key != old_key:
                    self.model.webapps[new_key] = self.model.webapps.pop(old_key)
                    self.model.webapps[new_key] = new_url  # Update URL too
            elif col == 1:  # URL changed
                self.model.webapps[new_key] = new_url

            self.model.webapps = self.model.webapps
            self._populate_table()  # Repopulate to ensure consistency

    def accept(self):
        """Save changes and close dialog."""
        try:
            # Update the model's webapps dictionary
            self.model.webapps = dict(self.model.webapps)

            # Save to configuration file
            self.model._save_endpoints(self.model.webapps)

            logger.info("Health check settings saved successfully")
            super().accept()
        except Exception as e:
            logger.error(f"Failed to save health check settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
