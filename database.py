"""
Database operations for the PostgreSQL Error Browser.
"""
from typing import Optional, List, Dict, Any, Tuple
import psycopg2
from psycopg2 import Error
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connection_timeout = 30  # seconds
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def connect(self, host: str, port: int, database: str, user: str, password: str) -> None:
        """
        Connect to the database with retry mechanism.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            
        Raises:
            Exception: If connection fails after all retries
        """
        for attempt in range(self.max_retries):
            try:
                if self.conn:
                    self.disconnect()
                    
                self.conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=database,
                    user=user,
                    password=password,
                    connect_timeout=self.connection_timeout
                )
                self.cursor = self.conn.cursor()
                logger.info(f"Successfully connected to database: {database}")
                return
                
            except Error as e:
                error_msg = str(e)
                logger.error(f"Connection attempt {attempt + 1} failed: {error_msg}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    import time
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed to connect after {self.max_retries} attempts: {error_msg}")
                    
    def disconnect(self) -> None:
        """Safely disconnect from the database."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            self.cursor = None
            self.conn = None
            logger.info("Successfully disconnected from database")
        except Error as e:
            logger.error(f"Error during disconnect: {str(e)}")
            raise
            
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self.conn is not None and not self.conn.closed
        
    def get_logs(self) -> List[Dict[str, Any]]:
        """
        Get all logs from the error_logs table.
        
        Returns:
            List of log entries as dictionaries
            
        Raises:
            Exception: If query fails
        """
        if not self.is_connected():
            raise Exception("Not connected to database")
            
        try:
            # First check if table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'error_logs'
                )
            """)
            
            if not self.cursor.fetchone()[0]:
                raise Exception("Table 'error_logs' does not exist")
                
            # Execute the main query
            self.cursor.execute('SELECT type, message, details FROM public.error_logs')
            columns = [desc[0] for desc in self.cursor.description]
            rows = self.cursor.fetchall()
            
            # Convert rows to list of dictionaries
            logs = []
            for row in rows:
                logs.append(dict(zip(columns, row)))
                
            return logs
            
        except Error as e:
            error_msg = str(e)
            logger.error(f"Query error: {error_msg}")
            raise Exception(f"Query failed: {error_msg}")
            
    def clear_logs(self) -> None:
        """
        Clear all records from the error_logs table.
        
        Raises:
            Exception: If operation fails
        """
        if not self.is_connected():
            raise Exception("Not connected to database")
            
        try:
            self.cursor.execute('TRUNCATE TABLE public.error_logs')
            self.conn.commit()
            logger.info("Successfully cleared error_logs table")
        except Error as e:
            self.conn.rollback()
            error_msg = str(e)
            logger.error(f"Clear table error: {error_msg}")
            raise Exception(f"Failed to clear table: {error_msg}")
            
    def get_table_info(self) -> Dict[str, Any]:
        """
        Get information about the error_logs table.
        
        Returns:
            Dictionary containing table information
            
        Raises:
            Exception: If operation fails
        """
        if not self.is_connected():
            raise Exception("Not connected to database")
            
        try:
            # Get column information
            self.cursor.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'error_logs'
                ORDER BY ordinal_position
            """)
            
            columns = []
            for row in self.cursor.fetchall():
                col_info = {
                    'name': row[0],
                    'type': row[1],
                    'max_length': row[2]
                }
                columns.append(col_info)
                
            # Get row count
            self.cursor.execute('SELECT COUNT(*) FROM public.error_logs')
            row_count = self.cursor.fetchone()[0]
            
            info = {
                'name': 'error_logs',
                'columns': columns,
                'row_count': row_count
            }
            
            return info
            
        except Error as e:
            error_msg = str(e)
            logger.error(f"Get table info error: {error_msg}")
            raise Exception(f"Failed to get table information: {error_msg}") 