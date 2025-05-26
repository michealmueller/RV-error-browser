"""
Database Viewer Application
--------------------------
A PySide6-based application for viewing PostgreSQL database tables with logging functionality.

Features:
- Connect to PostgreSQL databases
- Query and display table data
- Real-time logging with timestamps
- Clear log functionality
- Auto-scrolling log window
- Dynamic table column headers
- Pre-configured database connections

Usage:
1. Enter PostgreSQL connection details
2. Enter the table name to query
3. Click 'Connect' to establish database connection
4. Click 'Get Logs' to fetch and display table data
5. Use 'Clear Log' to reset the log window
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from app import DatabaseApp

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('quantumops.log', encoding='utf-8')
        ]
    )

if __name__ == '__main__':
    setup_logging()
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec())
