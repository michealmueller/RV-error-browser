"""
Main entry point for the PostgreSQL Error Browser - QuantumOps.
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from quantumops.main_window import MainWindow
from quantumops.theming import setup_qdarktheme

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
    logger.info("QuantumOps starting up")

    app = QApplication(sys.argv)
    
    # Apply modern theme - DISABLED to use custom colorful styling
    # try:
    #     setup_qdarktheme('light')  # Default theme
    # except Exception as e:
    #     logger.warning(f"Theme setup not available: {e}, using default theme")

    window = MainWindow()
    window.show()
    logger.info("Starting QuantumOps event loop")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
