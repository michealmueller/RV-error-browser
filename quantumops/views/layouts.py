from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QSplitter, QLabel, QPushButton, QGroupBox, QGridLayout
from PySide6.QtCore import Qt
from quantumops.views.build_view import BuildView

class ClassicTabbedLayout(QWidget):
    """Classic tabbed layout with tabs for Android/iOS builds, logs, and health."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.android_tab = BuildView("android")
        self.ios_tab = BuildView("ios")
        self.tab_widget.addTab(self.android_tab, "Android")
        self.tab_widget.addTab(self.ios_tab, "iOS")
        self.tab_widget.addTab(QLabel("Logs"), "Logs")
        self.tab_widget.addTab(QLabel("Health"), "Health")
        layout.addWidget(self.tab_widget)

class SplitViewLayout(QWidget):
    """Split view layout with side-by-side panels for builds and logs, and a collapsible health sidebar."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Horizontal)
        self.builds_panel = QLabel("Builds Panel")
        self.logs_panel = QLabel("Logs Panel")
        self.health_panel = QLabel("Health Panel")
        self.splitter.addWidget(self.builds_panel)
        self.splitter.addWidget(self.logs_panel)
        self.splitter.addWidget(self.health_panel)
        layout.addWidget(self.splitter)

class DashboardLayout(QWidget):
    """Dashboard layout with cards/widgets for builds, logs, health, and quick actions."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        self.builds_card = QGroupBox("Builds")
        self.logs_card = QGroupBox("Logs")
        self.health_card = QGroupBox("Health")
        self.actions_card = QGroupBox("Quick Actions")
        layout.addWidget(self.builds_card, 0, 0)
        layout.addWidget(self.logs_card, 0, 1)
        layout.addWidget(self.health_card, 1, 0)
        layout.addWidget(self.actions_card, 1, 1) 