"""
Main entry point for the PostgreSQL Error Browser.
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app import DatabaseApp
from theme import ThemeManager

def setup_logging():
    log_dir = Path.home() / '.postgres_error_browser' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'app.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Application starting up")

    app = QApplication(sys.argv)
    theme_manager = ThemeManager()
    theme_manager.apply_theme(app, 'light')  # Default theme

    window = DatabaseApp()
    window.show()
    logger.info("Starting application event loop")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
