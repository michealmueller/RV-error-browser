"""
Main entry point for the QuantumOps application.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from quantumops.views.main_window import MainWindow
from quantumops.controllers.main_controller import MainController
from quantumops.models.build_manager import BuildManager

def main():
    """Main application entry point."""
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
