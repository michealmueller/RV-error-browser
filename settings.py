"""
Settings management for the PostgreSQL Error Browser.
"""
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self):
        self.settings_dir = Path.home() / '.postgres_error_browser'
        self.settings_file = self.settings_dir / 'settings.json'
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                logger.info("Settings loaded successfully")
                return settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            
        # Default settings
        return {
            'connections': [],
            'last_connection': None,
            'window_geometry': None,
            'splitter_state': None,
            'theme': 'light',
            'font_size': 10,
            'auto_connect': False,
            'auto_refresh': False,
            'refresh_interval': 30,  # seconds
            'max_log_entries': 1000,
            'log_level': 'INFO'
        }
        
    def _ensure_settings_dir(self) -> None:
        """Ensure the settings directory exists."""
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create settings directory: {str(e)}")
            
    def save_settings(self) -> None:
        """Save settings to file."""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
        
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
        self.save_settings()
        
    def add_connection(self, connection: Dict[str, Any]) -> None:
        """
        Add a new connection to settings.
        
        Args:
            connection: Connection details
        """
        connections = self.settings.get('connections', [])
        # Remove if connection with same name exists
        connections = [c for c in connections if c.get('name') != connection.get('name')]
        connections.append(connection)
        self.settings['connections'] = connections
        self.save_settings()
        
    def remove_connection(self, name: str) -> None:
        """
        Remove a connection from settings.
        
        Args:
            name: Connection name
        """
        connections = self.settings.get('connections', [])
        connections = [c for c in connections if c.get('name') != name]
        self.settings['connections'] = connections
        if self.settings.get('last_connection') == name:
            self.settings['last_connection'] = None
        self.save_settings()
        
    def get_connection(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get connection details by name.
        
        Args:
            name: Connection name
            
        Returns:
            Connection details or None if not found
        """
        connections = self.settings.get('connections', [])
        for conn in connections:
            if conn.get('name') == name:
                return conn
        return None
        
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """
        Get all saved connections.
        
        Returns:
            List of connection details
        """
        return self.settings.get('connections', [])
        
    def set_last_connection(self, name: str) -> None:
        """
        Set the last used connection.
        
        Args:
            name: Connection name
        """
        self.settings['last_connection'] = name
        self.save_settings()
        
    def get_last_connection(self) -> Optional[str]:
        """
        Get the last used connection name.
        
        Returns:
            Last connection name or None
        """
        return self.settings.get('last_connection')
        
    def set_window_geometry(self, geometry: str) -> None:
        """
        Save window geometry.
        
        Args:
            geometry: Window geometry string
        """
        self.settings['window_geometry'] = geometry
        self.save_settings()
        
    def get_window_geometry(self) -> Optional[str]:
        """
        Get saved window geometry.
        
        Returns:
            Window geometry string or None
        """
        return self.settings.get('window_geometry')
        
    def set_splitter_state(self, state: bytes) -> None:
        """
        Save splitter state.
        
        Args:
            state: Splitter state bytes
        """
        self.settings['splitter_state'] = state.toHex().data().decode()
        self.save_settings()
        
    def get_splitter_state(self) -> Optional[bytes]:
        """
        Get saved splitter state.
        
        Returns:
            Splitter state bytes or None
        """
        state = self.settings.get('splitter_state')
        if state:
            return bytes.fromhex(state)
        return None 