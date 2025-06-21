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

from logging_utils import setup_logging
from views.main_window import MainWindow


def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()

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

    # Show window
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
