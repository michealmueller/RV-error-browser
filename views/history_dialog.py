"""
Dialog for displaying build history.
"""
from datetime import datetime
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class HistoryDialog(QDialog):
    """Dialog for displaying build history."""

    def __init__(self, history_manager, parent=None):
        """Initialize history dialog."""
        super().__init__(parent)
        self.history_manager = history_manager
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("Build History")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # Filters
        filter_layout = QHBoxLayout()

        self.platform_filter = QComboBox()
        self.platform_filter.addItems(["All Platforms", "Android", "iOS"])
        self.platform_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Platform:"))
        filter_layout.addWidget(self.platform_filter)

        self.operation_filter = QComboBox()
        self.operation_filter.addItems(
            ["All Operations", "Download", "Upload", "Install", "Share"]
        )
        self.operation_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Operation:"))
        filter_layout.addWidget(self.operation_filter)

        filter_layout.addStretch()

        # Export button
        self.export_button = QPushButton("Export History")
        self.export_button.clicked.connect(self.export_history)
        filter_layout.addWidget(self.export_button)

        layout.addLayout(filter_layout)

        # History table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Timestamp",
                "Build ID",
                "Platform",
                "Version",
                "Operation",
                "Status",
                "Details",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.clear_button = QPushButton("Clear History")
        self.clear_button.clicked.connect(self.clear_history)
        button_layout.addWidget(self.clear_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def load_history(self):
        """Load history into table."""
        history = self.history_manager.get_recent_history()
        self.update_table(history)

    def update_table(self, history: List[Dict[str, Any]]):
        """Update table with history data."""
        self.table.setRowCount(len(history))

        for row, entry in enumerate(history):
            # Timestamp
            timestamp = datetime.fromisoformat(entry["timestamp"])
            self.table.setItem(
                row, 0, QTableWidgetItem(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            )

            # Build ID
            self.table.setItem(row, 1, QTableWidgetItem(entry["build_id"]))

            # Platform
            self.table.setItem(row, 2, QTableWidgetItem(entry["platform"]))

            # Version
            self.table.setItem(row, 3, QTableWidgetItem(entry["version"]))

            # Operation
            self.table.setItem(
                row, 4, QTableWidgetItem(entry["operation"].capitalize())
            )

            # Status
            status_item = QTableWidgetItem(entry["status"].capitalize())
            status_item.setForeground(
                Qt.green if entry["status"] == "success" else Qt.red
            )
            self.table.setItem(row, 5, status_item)

            # Details
            details = []
            if entry.get("error_message"):
                details.append(f"Error: {entry['error_message']}")
            if entry.get("details"):
                for key, value in entry["details"].items():
                    details.append(f"{key}: {value}")
            self.table.setItem(row, 6, QTableWidgetItem("\n".join(details)))

        self.table.resizeColumnsToContents()

    def apply_filters(self):
        """Apply filters to history."""
        platform = self.platform_filter.currentText()
        operation = self.operation_filter.currentText()

        history = self.history_manager.get_recent_history()

        if platform != "All Platforms":
            history = [h for h in history if h["platform"] == platform]

        if operation != "All Operations":
            history = [h for h in history if h["operation"] == operation.lower()]

        self.update_table(history)

    def clear_history(self):
        """Clear history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self.load_history()

    def export_history(self):
        """Export history to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                self.history_manager.export_history(file_path)
                QMessageBox.information(
                    self, "Export Successful", f"History exported to {file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Failed", f"Failed to export history: {str(e)}"
                )
