"""
Unit tests for MainWindow.
"""
import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox
from PySide6.QtCore import Qt
from quantumops.views.main_window import MainWindow
from quantumops.views.build_view import BuildView
from quantumops.models.database import Database

@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    with patch("quantumops.models.database.Database") as mock:
        mock_db = Mock(spec=Database)
        mock_db.connect = Mock()
        mock_db.disconnect = Mock()
        mock.return_value = mock_db
        yield mock_db

@pytest.fixture
def build_view(app):
    """Create a BuildView instance."""
    return BuildView(platform="android")

@pytest.fixture
def main_window(app):
    """Create a MainWindow instance."""
    with patch('quantumops.models.database.Database') as mock_db:
        mock_db.return_value = Mock()
        return MainWindow(["TestApp"])

def test_init(main_window):
    """Test MainWindow initialization."""
    assert main_window is not None
    assert main_window.windowTitle() == "QuantumOps"

def test_setup_menu(main_window):
    """Test menu setup."""
    assert main_window.menuBar() is not None
    assert len(main_window.menuBar().actions()) > 0

def test_handle_about(qtbot, main_window):
    """Test the about button handler."""
    with patch('quantumops.views.main_window.QMessageBox.about') as mock_about:
        # Click the about button using qtbot
        qtbot.mouseClick(main_window.about_button, Qt.LeftButton)
        
        # Wait for any pending events
        qtbot.wait(100)
        
        # Verify the about dialog was called
        mock_about.assert_called_once()
        assert "About" in mock_about.call_args[0][1]

def test_handle_exit(main_window):
    """Test exit handling."""
    with patch('PySide6.QtWidgets.QApplication.quit') as mock_quit:
        main_window._handle_exit()
        mock_quit.assert_called_once()

def test_handle_azure_config(main_window):
    """Test Azure configuration dialog."""
    with patch('quantumops.views.azure_config_dialog.AzureConfigDialog') as mock_dialog:
        mock_dialog.return_value.exec.return_value = True
        main_window._handle_azure_config()
        mock_dialog.assert_called_once()

def test_handle_view_sp_info(main_window):
    """Test service principal info dialog."""
    with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info:
        main_window._handle_view_sp_info()
        mock_info.assert_called_once()

def test_handle_refresh(main_window):
    """Test refresh handling."""
    with patch.object(main_window, '_refresh_builds') as mock_refresh:
        main_window._handle_refresh()
        mock_refresh.assert_called_once()

def test_handle_platform_change(main_window):
    """Test platform change handling."""
    with patch.object(main_window, '_refresh_builds') as mock_refresh:
        main_window._handle_platform_change("ios")
        mock_refresh.assert_called_once()

def test_handle_error(main_window):
    """Test error handling."""
    with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical:
        main_window._handle_error("Test Error")
        mock_critical.assert_called_once()

def test_handle_status_update(main_window):
    """Test status update handling."""
    main_window._handle_status_update("Test Status")
    assert main_window.statusBar().currentMessage() == "Test Status"

def test_cleanup(main_window, mock_db):
    """Test cleanup."""
    main_window.cleanup()
    mock_db.disconnect.assert_called_once() 