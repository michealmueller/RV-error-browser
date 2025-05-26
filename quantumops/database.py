"""
Database connection and query logic for QuantumOps.
"""
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QSettings
import psycopg2
from psycopg2 import Error
import logging

logger = logging.getLogger(__name__)
logger.info("Loaded quantumops.database module.")

def load_connections(settings: Optional[QSettings] = None) -> List[Dict[str, Any]]:
    logger.info("Called load_connections()")
    if settings is None:
        settings = QSettings()
    connections = settings.value('connections')
    logger.info(f"Loading connections from QSettings: {connections}")
    return connections if connections else []

def save_connections(connections: List[Dict[str, Any]], settings: Optional[QSettings] = None) -> None:
    logger.info(f"Called save_connections() with {len(connections)} connections.")
    if settings is None:
        settings = QSettings()
    logger.info(f"Saving connections to QSettings: {connections}")
    settings.setValue('connections', connections)
    settings.sync()

def connect_to_database(host: str, port: str, dbname: str, user: str, password: str):
    logger.info(f"Called connect_to_database(host={host}, port={port}, dbname={dbname}, user={user})")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        logger.info(f"Successfully connected to database: {dbname}")
        return conn
    except Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def disconnect_database(conn) -> None:
    logger.info("Called disconnect_database()")
    if conn:
        conn.close()
        logger.info("Disconnected from database.")

def query_table(conn, table_name: str) -> List[tuple]:
    logger.info(f"Called query_table(table_name={table_name})")
    try:
        cursor = conn.cursor()
        cursor.execute(f'SELECT type, message, details FROM public.{table_name}')
        data = cursor.fetchall()
        logger.info(f"Fetched {len(data)} rows from table {table_name}")
        return data
    except Error as e:
        logger.error(f"Error querying table {table_name}: {e}")
        raise 