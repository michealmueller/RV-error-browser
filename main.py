"""
Main entry point for the QuantumOps application.
"""
import sys
import logging
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from quantumops.views.main_window import MainWindow
from quantumops.controllers.main_controller import MainController
from quantumops.models.build_manager import BuildManager

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
        
        # Load version
        version_file = project_root / "config" / "version.txt"
        if version_file.exists():
            with open(version_file, "r") as f:
                version = f.read().strip()
                app.setApplicationVersion(version)
                logger.info(f"Running QuantumOps version {version}")
        
        # Create main window
        window = MainWindow()
        
        # Create model and controller
        model = BuildManager()
        controller = MainController(model, window)
        
        # Show window
        window.show()
        logger.info("Application started successfully")
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
