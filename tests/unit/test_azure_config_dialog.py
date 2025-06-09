import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
from quantumops.views.azure_config_dialog import AzureConfigDialog
import io

@pytest.fixture
def azure_config_dialog(app):
    """Create an AzureConfigDialog instance."""
    return AzureConfigDialog()

def test_init(azure_config_dialog):
    """Test dialog initialization."""
    assert azure_config_dialog.windowTitle() == "Azure Configuration"
    assert azure_config_dialog.tenant_id_input is not None
    assert azure_config_dialog.client_id_input is not None
    assert azure_config_dialog.client_secret_input is not None
    assert azure_config_dialog.container_input is not None
    assert azure_config_dialog.storage_account_input is not None

def test_load_settings(azure_config_dialog):
    """Test loading settings from QSettings."""
    with patch('quantumops.views.azure_config_dialog.QSettings') as mock_settings:
        mock_settings.return_value.value.side_effect = [
            "test_tenant",
            "test_client",
            "test_secret",
            "test_container",
            "test_storage"
        ]
        azure_config_dialog._load_settings()
        
        assert azure_config_dialog.tenant_id_input.text() == "test_tenant"
        assert azure_config_dialog.client_id_input.text() == "test_client"
        assert azure_config_dialog.client_secret_input.text() == "test_secret"
        assert azure_config_dialog.container_input.text() == "test_container"
        assert azure_config_dialog.storage_account_input.text() == "test_storage"

def test_save_settings(azure_config_dialog):
    """Test saving settings to QSettings."""
    # Set test values
    azure_config_dialog.tenant_id_input.setText("test_tenant")
    azure_config_dialog.client_id_input.setText("test_client")
    azure_config_dialog.client_secret_input.setText("test_secret")
    azure_config_dialog.container_input.setText("test_container")
    azure_config_dialog.storage_account_input.setText("test_storage")
    
    with patch('quantumops.views.azure_config_dialog.QSettings') as mock_settings:
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance
        azure_config_dialog._save_settings()
        
        # Verify settings were saved
        mock_settings_instance.setValue.assert_any_call("azure/tenant_id", "test_tenant")
        mock_settings_instance.setValue.assert_any_call("azure/client_id", "test_client")
        mock_settings_instance.setValue.assert_any_call("azure/client_secret", "test_secret")
        mock_settings_instance.setValue.assert_any_call("azure/container", "test_container")
        mock_settings_instance.setValue.assert_any_call("azure/storage_account", "test_storage")

def test_validate_inputs(azure_config_dialog):
    """Test input validation."""
    # Test empty inputs
    azure_config_dialog.tenant_id_input.setText("")
    azure_config_dialog.client_id_input.setText("")
    azure_config_dialog.client_secret_input.setText("")
    azure_config_dialog.container_input.setText("")
    azure_config_dialog.storage_account_input.setText("")
    assert not azure_config_dialog._validate_inputs()
    
    # Test valid inputs
    azure_config_dialog.tenant_id_input.setText("test_tenant")
    azure_config_dialog.client_id_input.setText("test_client")
    azure_config_dialog.client_secret_input.setText("test_secret")
    azure_config_dialog.container_input.setText("test_container")
    azure_config_dialog.storage_account_input.setText("test_storage")
    assert azure_config_dialog._validate_inputs()

def test_handle_save(azure_config_dialog):
    """Test save button handling."""
    # Set test values
    azure_config_dialog.tenant_id_input.setText("test_tenant")
    azure_config_dialog.client_id_input.setText("test_client")
    azure_config_dialog.client_secret_input.setText("test_secret")
    azure_config_dialog.container_input.setText("test_container")
    azure_config_dialog.storage_account_input.setText("test_storage")
    
    with patch.object(azure_config_dialog, '_save_settings') as mock_save:
        azure_config_dialog._handle_save()
        mock_save.assert_called_once()
        assert azure_config_dialog.result() == 1  # Accepted

def test_handle_cancel(azure_config_dialog):
    """Test cancel button handling."""
    azure_config_dialog._handle_cancel()
    assert azure_config_dialog.result() == 0  # Rejected

def test_handle_test_connection(qtbot, azure_config_dialog, mock_azure_service):
    """Test the test connection button handler."""
    # Set up test data
    azure_config_dialog.account_name_input.setText("testaccount")
    azure_config_dialog.account_key_input.setText("testkey")
    azure_config_dialog.container_input.setText("testcontainer")
    
    # Mock the Azure service test_connection method
    mock_azure_service.test_connection.return_value = True
    
    # Click the test button using qtbot
    qtbot.mouseClick(azure_config_dialog.test_button, Qt.LeftButton)
    
    # Wait for any pending events
    qtbot.wait(100)
    
    # Verify the Azure service was called with correct parameters
    mock_azure_service.test_connection.assert_called_once_with(
        "testaccount",
        "testkey",
        "testcontainer"
    )
    
    # Verify the success message was shown
    assert azure_config_dialog.status_label.text() == "Connection successful!"

def test_handle_test_connection_failure(azure_config_dialog):
    """Test connection testing failure."""
    # Set test values
    azure_config_dialog.tenant_id_input.setText("test_tenant")
    azure_config_dialog.client_id_input.setText("test_client")
    azure_config_dialog.client_secret_input.setText("test_secret")
    azure_config_dialog.container_input.setText("test_container")
    azure_config_dialog.storage_account_input.setText("test_storage")
    
    with patch('quantumops.services.azure_service.AzureService') as mock_service:
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.initialize.side_effect = Exception("Test error")
        
        with patch('quantumops.views.azure_config_dialog.QMessageBox.critical') as mock_critical:
            azure_config_dialog._handle_test_connection()
            mock_critical.assert_called_once()
            # The dialog uses 'Error' as the title, so check the message argument
            assert "Connection failed" in mock_critical.call_args[0][2] 