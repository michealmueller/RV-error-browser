"""
Database model for handling PostgreSQL connections and queries.
"""
import logging
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class DatabaseModel(QObject):
    """Model for database operations."""
    
    # Signals
    connection_status_changed = Signal(bool, str)  # (connected, message)
    query_results_ready = Signal(list)  # List of dict results
    error_occurred = Signal(str)  # Error message
    
    def __init__(self):
        super().__init__()
        self._connection: Optional[psycopg2.extensions.connection] = None
        self._cursor: Optional[psycopg2.extensions.cursor] = None
        self._connected = False
        
    @property
    def is_connected(self) -> bool:
        """Return whether we're connected to the database."""
        return self._connected
        
    def connect(self, host: str, port: int, database: str, user: str, password: str) -> None:
        """Connect to the PostgreSQL database."""
        try:
            if self._connection:
                self.disconnect()
                
            self._connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                cursor_factory=RealDictCursor
            )
            self._cursor = self._connection.cursor()
            self._connected = True
            self.connection_status_changed.emit(True, "Connected successfully")
            logger.info(f"Connected to database {database} on {host}:{port}")
            
        except Exception as e:
            self._connected = False
            error_msg = f"Failed to connect: {str(e)}"
            self.connection_status_changed.emit(False, error_msg)
            self.error_occurred.emit(error_msg)
            logger.error(error_msg)
            
    def disconnect(self) -> None:
        """Disconnect from the database."""
        try:
            if self._cursor:
                self._cursor.close()
            if self._connection:
                self._connection.close()
            self._connected = False
            self.connection_status_changed.emit(False, "Disconnected")
            logger.info("Disconnected from database")
            
        except Exception as e:
            error_msg = f"Error during disconnect: {str(e)}"
            self.error_occurred.emit(error_msg)
            logger.error(error_msg)
            
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Execute a query and emit results."""
        if not self._connected:
            self.error_occurred.emit("Not connected to database")
            return
            
        try:
            self._cursor.execute(query, params or {})
            results = self._cursor.fetchall()
            self.query_results_ready.emit(results)
            logger.info(f"Query executed successfully: {query[:100]}...")
            
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            self.error_occurred.emit(error_msg)
            logger.error(error_msg)
            
    def get_tables(self) -> List[str]:
        """Get list of tables in the database."""
        if not self._connected:
            return []
            
        try:
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """
            self._cursor.execute(query)
            return [row['table_name'] for row in self._cursor.fetchall()]
            
        except Exception as e:
            error_msg = f"Failed to get tables: {str(e)}"
            self.error_occurred.emit(error_msg)
            logger.error(error_msg)
            return [] 