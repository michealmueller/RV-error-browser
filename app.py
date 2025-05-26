"""
Main application window and logic for the database viewer.
"""

import sys
import logging
from datetime import datetime, timezone, timedelta
import psycopg2
from psycopg2 import Error
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QTableWidget,
    QTableWidgetItem, QFormLayout, QComboBox, QMessageBox,
    QSplitter, QDialog, QMenuBar, QMenu, QDialogButtonBox, QTextEdit,
    QFrame, QTabWidget, QSizePolicy, QProgressBar, QFileDialog, QTreeWidget, QTreeWidgetItem, QStyle
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QPalette, QColor, QFont, QTextCursor, QActionGroup
from PySide6.QtWidgets import QApplication
import subprocess
import json
import os
import shutil
from urllib.parse import urlparse, parse_qs
from azure.storage.blob import BlobClient
import requests
import re
import qdarktheme
from quantumops.main_window import DatabaseApp

from delegates import DetailsDelegate, format_details
from dialogs import ConnectionDialog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    import sys
    app = QApplication(sys.argv)
    DatabaseApp.setup_qdarktheme("light")  # Default to light theme
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 