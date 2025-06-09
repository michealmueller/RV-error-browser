"""
Database model for QuantumOps.
"""
import psycopg2
from psycopg2.extras import DictCursor
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database model for QuantumOps."""
    
    def __init__(self, config: Dict[str, str]):
        """Initialize database connection.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.conn = None
        self.connect()
    
    def connect(self) -> None:
        """Connect to the database."""
        try:
            self.conn = psycopg2.connect(**self.config)
            self.conn.autocommit = True
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        """Execute a query.
        
        Args:
            query: SQL query
            params: Query parameters
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
        except psycopg2.Error as e:
            logger.error(f"Failed to execute query: {e}")
            raise
    
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch one row from the database.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Dictionary containing row data or None if no row found
        """
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query, params)
                return dict(cur.fetchone()) if cur.rowcount > 0 else None
        except psycopg2.Error as e:
            logger.error(f"Failed to fetch row: {e}")
            raise
    
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all rows from the database.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of dictionaries containing row data
        """
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error as e:
            logger.error(f"Failed to fetch rows: {e}")
            raise
    
    def insert_build(self, build_id: str, platform: str, version: str, status: str) -> None:
        """Insert a build record.
        
        Args:
            build_id: Build ID
            platform: Platform (android/ios)
            version: Version number
            status: Build status
        """
        query = """
            INSERT INTO builds (build_id, platform, version, status)
            VALUES (%s, %s, %s, %s)
        """
        self.execute(query, (build_id, platform, version, status))
    
    def update_build_status(self, build_id: str, status: str) -> None:
        """Update build status.
        
        Args:
            build_id: Build ID
            status: New status
        """
        query = """
            UPDATE builds
            SET status = %s
            WHERE build_id = %s
        """
        self.execute(query, (status, build_id))
    
    def get_build(self, build_id: str) -> Optional[Dict[str, Any]]:
        """Get build by ID.
        
        Args:
            build_id: Build ID
            
        Returns:
            Build data dictionary or None if not found
        """
        query = """
            SELECT *
            FROM builds
            WHERE build_id = %s
        """
        return self.fetch_one(query, (build_id,))
    
    def get_builds(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all builds.
        
        Args:
            platform: Optional platform filter
            
        Returns:
            List of build data dictionaries
        """
        query = """
            SELECT *
            FROM builds
        """
        params = None
        if platform:
            query += " WHERE platform = %s"
            params = (platform,)
        query += " ORDER BY created_at DESC"
        return self.fetch_all(query, params)
    
    def add_history(self, build_id: str, platform: str, version: str, action: str, status: str) -> None:
        """Add history record.
        
        Args:
            build_id: Build ID
            platform: Platform (android/ios)
            version: Version number
            action: Action performed
            status: Action status
        """
        query = """
            INSERT INTO history (build_id, platform, version, action, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.execute(query, (build_id, platform, version, action, status))
    
    def get_history(self, build_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get history records.
        
        Args:
            build_id: Optional build ID filter
            
        Returns:
            List of history data dictionaries
        """
        query = """
            SELECT *
            FROM history
        """
        params = None
        if build_id:
            query += " WHERE build_id = %s"
            params = (build_id,)
        query += " ORDER BY created_at DESC"
        return self.fetch_all(query, params) 