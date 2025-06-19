"""
Logging helpers for QuantumOps: append lines to a QTextBrowser with color coding.
"""
from PySide6.QtWidgets import QTextBrowser
from PySide6.QtGui import QTextCursor
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logger.info("Loaded quantumops.logging_utils module.")

def append_terminal_line(log_window: QTextBrowser, line: str, msg_type: str = "info", log_enabled: Optional[bool] = True) -> None:
    """Append a colored line to the QTextBrowser log window."""
    logger.info(f"Called append_terminal_line(msg_type={msg_type}, log_enabled={log_enabled}) | line: {line[:80]}")
    if not log_enabled:
        return
    log_window.moveCursor(QTextCursor.End)
    color = "#fff"  # default white
    if msg_type == "error":
        color = "#ff5555"  # red
    elif msg_type == "success":
        color = "#50fa7b"  # green
    elif msg_type == "system":
        color = "#bbbbbb"  # grey
    elif msg_type == "info":
        color = "#8be9fd"  # cyan/light blue for info
    log_window.append(f'<span style="color:{color};">{line.rstrip()}</span>')
    log_window.moveCursor(QTextCursor.End) 