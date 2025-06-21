"""
Log streaming model for QuantumOps.
"""
import logging
import threading

from PySide6.QtCore import QObject, Signal

from azure_webapp import AzureWebApp

logger = logging.getLogger(__name__)


class LogStreamModel(QObject):
    """Model for handling log streaming operations."""

    log_received = Signal(str)
    error_occurred = Signal(str)
    status_changed = Signal(str)  # For status updates

    def __init__(self, azure_webapp: AzureWebApp):
        super().__init__()
        self.azure_webapp = azure_webapp
        self.is_running = False
        self._log_buffer = []
        self._buffer_lock = threading.Lock()
        self._max_buffer_size = 1000

    def start_streaming(self, resource_group: str, web_app_name: str) -> None:
        """Start streaming logs from the specified web app."""
        if self.is_running:
            self.stop_streaming()

        self.is_running = True
        self.status_changed.emit("Starting log stream...")

        try:

            def log_callback(line: str):
                if not self.is_running:
                    return
                with self._buffer_lock:
                    self._log_buffer.append(line)
                    if len(self._log_buffer) > self._max_buffer_size:
                        self._log_buffer = self._log_buffer[-self._max_buffer_size :]
                self.log_received.emit(line)

            self.azure_webapp.stream_logs(
                resource_group, web_app_name, callback=log_callback
            )
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.status_changed.emit(f"Error: {str(e)}")
        finally:
            self.is_running = False
            self.status_changed.emit("Log stream stopped")

    def stop_streaming(self) -> None:
        """Stop the log streaming."""
        self.is_running = False
        with self._buffer_lock:
            self._log_buffer.clear()
        self.status_changed.emit("Stopping log stream...")

    def get_log_buffer(self) -> list:
        """Get the current log buffer."""
        with self._buffer_lock:
            return self._log_buffer.copy()

    def clear_buffer(self) -> None:
        """Clear the log buffer."""
        with self._buffer_lock:
            self._log_buffer.clear()
