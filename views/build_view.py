"""
Build view for displaying and managing mobile builds.
"""
import logging
from datetime import datetime

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class BuildView(QWidget):
    """View for displaying and managing mobile builds."""

    # Signals
    build_selected = Signal(str)  # build_id
    filter_changed = Signal(dict)  # filter criteria
    fetch_requested = Signal()
    download_requested = Signal(str)
    push_to_azure_requested = Signal(str)
    install_requested = Signal(str)
    share_requested = Signal(str)  # build_id

    def __init__(self, platform: str, parent: QWidget = None):
        super().__init__(parent)
        self.platform = platform
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._create_widgets()
        self._setup_layout()
        self._setup_connections()

    def _create_widgets(self):
        """Create UI widgets."""
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Build ID",
                "Version",
                "Version Code",
                "Channel",
                "Status",
                "Date",
                "Actions",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

    def _setup_layout(self):
        """Set up the layout."""
        self._layout.addWidget(self.table)

    def _setup_connections(self):
        """Set up signal-slot connections."""
        self.table.doubleClicked.connect(self._on_row_double_clicked)

    def show_loading(self):
        """Display a loading indicator in the table."""
        self.table.setRowCount(1)
        self.table.setSpan(0, 0, 1, self.table.columnCount())
        loading_item = QTableWidgetItem("Loading...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 0, loading_item)
        self.table.setEnabled(False)

    def hide_loading(self):
        """Hide the loading indicator and re-enable the table."""
        self.table.setRowCount(0)
        self.table.setEnabled(True)

    def _on_row_double_clicked(self, index):
        """Handle double-clicking a row."""
        # Placeholder for future implementation
        logger.info(f"Row {index.row()} double-clicked.")

    def _handle_search(self, text: str):
        """Handle search input changes."""
        try:
            self.filter_changed.emit(
                {
                    "search": text,
                    "version": self.version_filter.currentData(),
                    "status": self.status_filter.currentData(),
                }
            )
        except Exception as e:
            logger.error(f"Error handling search: {e}")
            self._show_error("Search Error", str(e))

    def _handle_filter_change(self):
        """Handle filter selection changes."""
        try:
            self.filter_changed.emit(
                {
                    "search": self.search_input.text(),
                    "version": self.version_filter.currentData(),
                    "status": self.status_filter.currentData(),
                }
            )
        except Exception as e:
            logger.error(f"Error handling filter change: {e}")
            self._show_error("Filter Error", str(e))

    def _handle_selection(self):
        """Handle build selection."""
        try:
            selected = self.builds_table.selectedItems()
            if selected:
                build_id = selected[0].text()
                self.build_selected.emit(build_id)
        except Exception as e:
            logger.error(f"Error handling selection: {e}")
            self._show_error("Selection Error", str(e))

    def _show_error(self, title: str, message: str):
        """Show error message to user."""
        QMessageBox.critical(self, title, message)

    @Slot(list)
    def update_builds(self, builds: list):
        """Update the table with new build data."""
        self.hide_loading()
        self.table.setRowCount(len(builds))
        for row, build in enumerate(builds):
            self._populate_row(row, build)
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()
        # Ensure the 'Actions' column has enough space for buttons
        self.table.setColumnWidth(6, 200)

    def _populate_row(self, row: int, build: dict):
        """Populate a single row in the table."""
        self.table.setItem(row, 0, QTableWidgetItem(build.get("id")))

        version_info = build.get("appVersion", "N/A")
        self.table.setItem(row, 1, QTableWidgetItem(version_info))

        version_code = build.get("appBuildVersion", "N/A")
        self.table.setItem(row, 2, QTableWidgetItem(version_code))

        self.table.setItem(row, 3, QTableWidgetItem(build.get("channel", "N/A")))
        self.table.setItem(row, 4, QTableWidgetItem(build.get("status", "N/A")))

        date_str = build.get("createdAt", "")
        if date_str:
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        self.table.setItem(row, 5, QTableWidgetItem(date_str))

        self._add_action_buttons(row, build.get("id"))

    def _add_action_buttons(self, row: int, build_id: str):
        """Add action buttons to a row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)

        # Stacked widget for download button and progress bar
        download_stack = QStackedWidget()
        download_stack.setFixedWidth(120)
        download_btn = QPushButton()
        download_btn.setIcon(QIcon(":/icons/download.svg"))
        download_btn.setToolTip("Download build")
        download_btn.setFixedWidth(40)
        download_btn.clicked.connect(lambda: self.download_requested.emit(build_id))
        download_stack.addWidget(download_btn)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        download_stack.addWidget(progress_bar)

        layout.addStretch()
        layout.addWidget(download_stack)

        # Push to Azure button
        push_btn = QPushButton()
        push_btn.setIcon(QIcon(":/icons/upload.svg"))
        push_btn.setToolTip("Push to Azure")
        push_btn.setFixedWidth(40)
        push_btn.clicked.connect(lambda: self.push_to_azure_requested.emit(build_id))
        layout.addWidget(push_btn)
        layout.addStretch()

        widget.setLayout(layout)
        self.table.setCellWidget(row, 6, widget)

    def show_download_progress(self, build_id: str):
        """Show a progress bar for a specific build."""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == build_id:
                widget = self.table.cellWidget(row, 6)
                if widget:
                    stack = widget.findChild(QStackedWidget)
                    if stack:
                        stack.setCurrentIndex(1)
                        return

    def update_download_progress(self, build_id: str, value: int):
        """Update the progress bar for a specific build."""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == build_id:
                widget = self.table.cellWidget(row, 6)
                if widget:
                    stack = widget.findChild(QStackedWidget)
                    if stack and stack.currentIndex() == 1:
                        progress_bar = stack.widget(1)
                        if isinstance(progress_bar, QProgressBar):
                            progress_bar.setValue(value)
                        return

    def hide_download_progress(self, build_id: str):
        """Hide the progress bar and show the download button."""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == build_id:
                widget = self.table.cellWidget(row, 6)
                if widget:
                    stack = widget.findChild(QStackedWidget)
                    if stack:
                        stack.setCurrentIndex(0)  # Index of the download button
                        return

    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def show_error(self, message: str):
        """Show an error message dialog."""
        QMessageBox.critical(self, "Error", message)

    def update_build_status(self, build_id: str, status: str):
        """Update the status of a specific build in the table."""
        try:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0).text() == build_id:
                    self.table.item(row, 4).setText(status)
                    break
        except Exception as e:
            logger.error(f"Error updating build status: {e}")

    def update_upload_status(self, build_id: str, status: str):
        """Update upload status for a build."""
        try:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0).text() == build_id:
                    # Update status column with upload info
                    current_status = self.table.item(row, 4).text()
                    self.table.item(row, 4).setText(f"{current_status} - {status}")
                    break
        except Exception as e:
            logger.error(f"Error updating upload status: {e}")

    def update_upload_retry(self, build_id: str, attempt: int):
        """Update upload retry information."""
        try:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0).text() == build_id:
                    current_status = self.table.item(row, 4).text()
                    self.table.item(row, 4).setText(
                        f"{current_status} - Retry {attempt}"
                    )
                    break
        except Exception as e:
            logger.error(f"Error updating upload retry: {e}")
