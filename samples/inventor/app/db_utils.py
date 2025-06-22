"""
Database utilities module for the VideoInventory application.
This module provides a centralized interface for all database operations,
including connection management, query execution, and schema initialization.
"""

import os
import sqlite3
import logging
import platform
from typing import Optional, Any, List, Tuple, Dict, Union
from app.sqlite_init import table_definitions

# Global connection object
_connection: Optional[sqlite3.Connection] = None
logger = logging.getLogger(__name__)

def get_connection(database_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish and return a global connection to the SQLite database.

    Args:
        database_path (str, optional): Path to the SQLite database. If None, uses environment
                                      variable DB_PATH or default path.

    Returns:
        sqlite3.Connection: A connection instance to interact with the database.
    """
    global _connection

    if _connection is None:
        # Determine database path
        if database_path is None:
            # Try to find the project root directory
            current_file = os.path.abspath(__file__)
            app_dir = os.path.dirname(current_file)
            project_root = os.path.dirname(app_dir)  # One level up from app dir

            # Create a data directory in the project root
            data_dir = os.path.join(project_root, "data")
            default_path = os.path.join(data_dir, "video_inventory.db")

            # Use environment variable if set, otherwise use default path
            database_path = os.environ.get('DB_PATH', default_path)

        # Create directory if it doesn't exist
        db_dir = os.path.dirname(database_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
            except OSError as e:
                logger.warning(f"Could not create database directory {db_dir}: {e}")
                # Fallback to project root if we can't create the data directory
                database_path = os.path.join(project_root, "video_inventory.db")
                logger.info(f"Using fallback database path: {database_path}")

        logger.info(f"Connecting to database at: {database_path}")
        _connection = sqlite3.connect(database_path)
        _connection.row_factory = sqlite3.Row  # Return results as dictionary-like objects

    return _connection


def execute_query(query: str, params: Tuple = (), fetch: bool = False) -> Union[List[Dict[str, Any]], None]:
    """
    Execute a SQL query with parameters.

    Args:
        query (str): The SQL query to execute.
        params (Tuple): Parameters to safely inject into the query.
        fetch (bool): Whether to return results (for SELECT queries).

    Returns:
        List[Dict[str, Any]] or None: Results if fetch is True, otherwise None.
    """
    connection = get_connection()

    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute(query, params)

            if fetch:
                results = cursor.fetchall()
                # Convert sqlite3.Row objects to dictionaries
                return [dict(row) for row in results]
            else:
                connection.commit()
                return None
    except sqlite3.Error as e:
        logger.error(f"Database error executing query: {e}")
        logger.debug(f"Failed query: {query} with params {params}")
        raise


def initialize_database(config=None) -> bool:
    """
    Initialize the database by creating required tables if they do not exist.

    Args:
        config: Optional configuration object

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Create tables from definitions
        for table_name, create_table_sql in table_definitions.items():
            logger.info(f"Creating table if not exists: {table_name}")
            cursor.execute(create_table_sql)

        connection.commit()
        logger.info("Database initialization completed successfully")
        return True

    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        return False


def close_connections() -> None:
    """
    Closes the global database connection.
    """
    global _connection
    if _connection:
        logger.info("Closing database connection")
        _connection.close()
        _connection = None


def get_db_connection() -> sqlite3.Connection:
    """
    Compatibility function for existing code that calls get_db_connection().
    Returns the global connection.
    """
    return get_connection()