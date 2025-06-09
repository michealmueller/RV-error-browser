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
        cursor.execute(f'SELECT "createdAt", type, message, details FROM public.{table_name}')
        data = cursor.fetchall()
        logger.info(f"Fetched {len(data)} rows from table {table_name}")
        return data
    except Error as e:
        logger.error(f"Error querying table {table_name}: {e}")
        raise

def update_download_url(conn, table: str, build_id: str, url: str) -> None:
    """
    Update the download_url for a build in the specified table by id.
    Args:
        conn: psycopg2 connection object
        table: table name (android_builds or ios_builds)
        build_id: the build's id (UUID or int as string)
        url: the download URL to set
    """
    logger.info(f"Updating download_url for build {build_id} in {table} to {url}")
    try:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE public.{table} SET download_url = %s WHERE id = %s', (url, build_id))
        conn.commit()
        logger.info(f"Updated download_url for build {build_id} in {table}")
    except Error as e:
        logger.error(f"Error updating download_url for build {build_id} in {table}: {e}")
        raise 