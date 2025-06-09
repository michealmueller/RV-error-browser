"""
Main application entry point for QuantumOps.
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from quantumops.views.main_window import MainWindow

def setup_logging():
    """Set up logging configuration."""
    log_dir = Path.home() / ".quantumops" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "quantumops.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("QuantumOps")
        app.setOrganizationName("Rosie Vision")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 