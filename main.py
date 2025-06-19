"""
Main entry point for the QuantumOps application.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from views.main_window import MainWindow
from controllers.build_controller import BuildController
from controllers.database_controller import DatabaseController
from controllers.health_controller import HealthController
from controllers.log_controller import LogController
from controllers.main_controller import MainController
from models.build_manager import BuildManager
from models.database import DatabaseModel
from models.health_check import HealthCheckModel
from models.history_manager import HistoryManager
from models.log_stream import LogStreamModel
from services.azure_service import AzureService

def main():
    """Main application entry point."""
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Environment variables loaded from .env file")
    except ImportError:
        print("python-dotenv not available, using system environment variables")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("QuantumOps")
    app.setOrganizationName("RosieVision")
    
    # Load version
    version_file = project_root / "config" / "version.txt"
    if version_file.exists():
        with open(version_file, "r") as f:
            version = f.read().strip()
            app.setApplicationVersion(version)
    
    # Create main window
    window = MainWindow()
    
    # Create model and controller
    model = BuildManager()
    controller = MainController(model, window)
    
    # Show window
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
