"""
Database controller for coordinating between model and view.
"""
import logging
from PySide6.QtCore import QObject
from models.database import DatabaseModel
from views.database_view import DatabaseView

logger = logging.getLogger(__name__)

class DatabaseController(QObject):
    """Controller for database operations."""
    
    def __init__(self, model: DatabaseModel, view: DatabaseView):
        super().__init__()
        self._model = model
        self._view = view
        
        # Connect model signals
        self._model.connection_status_changed.connect(self._view.update_connection_status)
        self._model.query_results_ready.connect(self._view.display_results)
        self._model.error_occurred.connect(self._view.show_error)
        
        # Connect view signals
        self._view.connect_requested.connect(self._model.connect)
        self._view.disconnect_requested.connect(self._model.disconnect)
        self._view.query_requested.connect(self._model.execute_query)
        
        logger.info("Database controller initialized")
        
    def cleanup(self):
        """Clean up resources."""
        if self._model.is_connected:
            self._model.disconnect()
        logger.info("Database controller cleaned up") 