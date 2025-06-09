"""
PostgreSQL Error Browser - Main Entry Point
"""
import sys
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app import DatabaseApp
from settings import SettingsManager
from theme import ThemeManager

def setup_logging():
    """Set up logging configuration."""
    # Create logs directory
    log_dir = Path.home() / '.postgres_error_browser' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up logging
    log_file = log_dir / 'app.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("Application starting up")
    
def main():
    """Main entry point for the application."""
    try:
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("PostgreSQL Error Browser")
        app.setApplicationVersion("1.0.0")
        
        # Load settings
        settings_manager = SettingsManager()
        theme_manager = ThemeManager()
        
        # Apply theme
        theme = settings_manager.get_setting('theme', 'light')
        theme_manager.apply_theme(app, theme)
        
        # Create and show main window
        window = DatabaseApp()
        window.show()
        
        # Start event loop
        logger.info("Starting application event loop")
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
        
if __name__ == "__main__":
    main()
