import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox
from PySide6.QtCore import Qt
from quantumops.views.main_window import MainWindow

@pytest.fixture
def main_window():
    """Create a MainWindow instance."""
    return MainWindow()

def test_init(main_window):
    """Test window initialization."""
    assert main_window.windowTitle() == "QuantumOps"
    assert main_window.android_model is not None
    assert main_window.ios_model is not None

def test_setup_menu(main_window):
    """Test menu setup."""
    assert main_window.menuBar() is not None
    file_menu = main_window.menuBar().findChild(QMenu, "File")
    assert file_menu is not None

def test_handle_about(main_window):
    """Test about dialog."""
    with patch('PySide6.QtWidgets.QMessageBox.about') as mock_about:
        main_window.show_about()
        mock_about.assert_called_once()

def test_handle_exit(main_window):
    """Test exit handling."""
    with patch('PySide6.QtWidgets.QMainWindow.close') as mock_close:
        main_window.close()
        mock_close.assert_called_once()

def test_handle_azure_config(main_window):
    """Test Azure configuration dialog."""
    with patch('quantumops.views.azure_config_dialog.AzureConfigDialog') as mock_dialog:
        main_window._show_sp_info()
        mock_dialog.assert_called_once()

def test_handle_view_sp_info(main_window):
    """Test viewing service principal info."""
    with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info:
        main_window._show_sp_info()
        mock_info.assert_called_once()

def test_handle_refresh(main_window):
    """Test refresh handling."""
    with patch.object(main_window.android_model, 'fetch_builds') as mock_android_fetch:
        with patch.object(main_window.ios_model, 'fetch_builds') as mock_ios_fetch:
            main_window.refresh_builds()
            mock_android_fetch.assert_called_once_with('android', force_refresh=True)
            mock_ios_fetch.assert_called_once_with('ios', force_refresh=True)

def test_handle_platform_change(main_window):
    """Test platform change handling."""
    with patch.object(main_window.android_model, 'fetch_builds') as mock_android_fetch:
        with patch.object(main_window.ios_model, 'fetch_builds') as mock_ios_fetch:
            main_window.platform_combo.setCurrentText("iOS")
            mock_ios_fetch.assert_called_once()
            main_window.platform_combo.setCurrentText("Android")
            mock_android_fetch.assert_called_once()

def test_handle_error(main_window):
    """Test error handling."""
    with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical:
        main_window._handle_error("Test Error")
        mock_critical.assert_called_once()
        assert "Test Error" in mock_critical.call_args[0][2]

def test_handle_status_update(main_window):
    """Test status bar updates."""
    main_window.show_status("Test status")
    assert main_window.statusBar().currentMessage() == "Test status"

def test_cleanup(main_window):
    """Test cleanup method."""
    with patch.object(main_window.android_controller, 'cleanup') as mock_android_cleanup:
        with patch.object(main_window.ios_controller, 'cleanup') as mock_ios_cleanup:
            main_window.close()
            mock_android_cleanup.assert_called_once()
            mock_ios_cleanup.assert_called_once() 