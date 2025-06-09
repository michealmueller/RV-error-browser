"""
Database controller for QuantumOps.
"""
from typing import Dict, List, Any, Optional
from PySide6.QtCore import QObject, Signal
from quantumops.models.database import Database

class DatabaseController(QObject):
    """Controller for database operations."""
    
    # Signals
    connection_status_changed = Signal(bool, str)  # (connected, message)
    query_results_ready = Signal(list)  # List of dict results
    error_occurred = Signal(str)  # Error message
    
    def __init__(self, db: Database):
        """Initialize database controller.
        
        Args:
            db: Database instance
        """
        super().__init__()
        self._db = db
    
    def connect(self, config: Dict[str, str]) -> None:
        """Connect to database.
        
        Args:
            config: Database configuration
        """
        try:
            self._db = Database(config)
            self.connection_status_changed.emit(True, "Connected successfully")
        except Exception as e:
            self.connection_status_changed.emit(False, str(e))
            self.error_occurred.emit(str(e))
    
    def close(self) -> None:
        """Close database connection."""
        try:
            self._db.close()
            self.connection_status_changed.emit(False, "Disconnected")
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def insert_build(self, build_id: str, platform: str, version: str, status: str) -> None:
        """Insert a build record.
        
        Args:
            build_id: Build ID
            platform: Platform (android/ios)
            version: Version number
            status: Build status
        """
        try:
            self._db.insert_build(build_id, platform, version, status)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def update_build_status(self, build_id: str, status: str) -> None:
        """Update build status.
        
        Args:
            build_id: Build ID
            status: New status
        """
        try:
            self._db.update_build_status(build_id, status)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def get_build(self, build_id: str) -> Optional[Dict[str, Any]]:
        """Get build by ID.
        
        Args:
            build_id: Build ID
            
        Returns:
            Build data dictionary or None if not found
        """
        try:
            return self._db.get_build(build_id)
        except Exception as e:
            self.error_occurred.emit(str(e))
            return None
    
    def get_builds(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all builds.
        
        Args:
            platform: Optional platform filter
            
        Returns:
            List of build data dictionaries
        """
        try:
            return self._db.get_builds(platform)
        except Exception as e:
            self.error_occurred.emit(str(e))
            return []
    
    def add_history(self, build_id: str, platform: str, version: str, action: str, status: str) -> None:
        """Add history record.
        
        Args:
            build_id: Build ID
            platform: Platform (android/ios)
            version: Version number
            action: Action performed
            status: Action status
        """
        try:
            self._db.add_history(build_id, platform, version, action, status)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def get_history(self, build_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get history records.
        
        Args:
            build_id: Optional build ID filter
            
        Returns:
            List of history data dictionaries
        """
        try:
            return self._db.get_history(build_id)
        except Exception as e:
            self.error_occurred.emit(str(e))
            return [] 