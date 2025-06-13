"""
Build Manager component for QuantumOps.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTextEdit,
    QHBoxLayout, QGroupBox
)
from PySide6.QtCore import Qt
from quantumops.builds import fetch_builds
import json

class BuildManager(QWidget):
    """A widget for managing and monitoring builds."""
    
    def __init__(self, parent: QWidget = None):
        """Initialize the BuildManager."""
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self) -> None:
        """Set up the UI for the build manager."""
        layout = QVBoxLayout()
        
        # Build controls
        controls_layout = QHBoxLayout()
        self.android_build_button = QPushButton("Build Android")
        self.ios_build_button = QPushButton("Build iOS")
        
        controls_layout.addWidget(self.android_build_button)
        controls_layout.addWidget(self.ios_build_button)
        
        # Build logs
        logs_groupbox = QGroupBox("Build Logs")
        logs_layout = QVBoxLayout()
        self.build_logs = QTextEdit()
        self.build_logs.setReadOnly(True)
        logs_layout.addWidget(self.build_logs)
        logs_groupbox.setLayout(logs_layout)
        
        layout.addLayout(controls_layout)
        layout.addWidget(logs_groupbox)
        
        self.setLayout(layout) 

    def connect_signals(self) -> None:
        """Connect UI signals to methods."""
        self.android_build_button.clicked.connect(lambda: self.trigger_build("android"))
        self.ios_build_button.clicked.connect(lambda: self.trigger_build("ios"))
        
    def trigger_build(self, platform: str) -> None:
        """Trigger a build for the specified platform."""
        self.build_logs.clear()
        self.build_logs.append(f"Fetching {platform} builds...")
        try:
            builds = fetch_builds(platform)
            self.build_logs.append(json.dumps(builds, indent=2))
        except Exception as e:
            self.build_logs.append(f"Error fetching builds: {e}") 