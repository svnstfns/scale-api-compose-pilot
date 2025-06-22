# app/database_utils.py
import time
import logging
import mysql.connector
from mysql.connector import Error, pooling
from typing import Optional, List, Dict, Any
from app.config import Config

logger = logging.getLogger(__name__)
_connection_pool = None


def _init_connection_pool(config: Config):
    global _connection_pool
    if _connection_pool is None:
        logger.debug("_init_connection_pool: Erstelle Connection-Pool")
        _connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="videoinventory_pool",
            pool_size=config.thread_count + 2,
            **config.db_config
        )
        logger.info(f"Connection-Pool mit Größe {config.thread_count + 2} erstellt")


def get_connection(config: Optional[Config] = None):
    global _connection_pool
    if config is None:
        config = Config()
    _init_connection_pool(config)
    return _connection_pool.get_connection()


def initialize_database(logger: logging.Logger, config: Optional[Config] = None):
    logger.debug("initialize_database: Starte Initialisierung")
    if config is None:
        config = Config()

    try:
        # Verbindung prüfen
        conn = mysql.connector.connect(**config.db_config)
        conn.close()
        logger.info("Verbindung zur Datenbank erfolgreich")
    except Error as e:
        logger.error(f"Verbindung zur Datenbank fehlgeschlagen: {e}")
        raise ConnectionError("Konnte keine Verbindung zur Datenbank herstellen")

    _init_connection_pool(config)
    ensure_tables_exist(logger, config)


def ensure_tables_exist(logger: logging.Logger, config: Optional[Config] = None) -> None:
    logger.debug("ensure_tables_exist: Aufgerufen")
    if config is None:
        config = Config()

    table_schemas = config.get_required_tables()
    logger.debug(f"ensure_tables_exist: Tabellen-Schema geladen: {list(table_schemas.keys())}")

    try:
        conn = get_connection(config)
        cursor = conn.cursor()
        logger.debug("ensure_tables_exist: Verbindung hergestellt und Cursor erstellt")

        cursor.execute("SHOW TABLES")
        existing_tables = set(row[0] for row in cursor.fetchall())
        logger.debug(f"Bereits existierende Tabellen: {existing_tables}")

        for table_name, schema in table_schemas.items():
            if table_name in existing_tables:
                logger.info(f"Tabelle '{table_name}' existiert bereits, wird übersprungen.")
                continue

            logger.info(f"Erstelle Tabelle: {table_name}")
            logger.debug(f"SQL: {schema}")
            cursor.execute(schema)
            conn.commit()
            logger.info(f"Tabelle '{table_name}' wurde erstellt.")

        cursor.close()
        conn.close()
        logger.debug("ensure_tables_exist: Verbindung und Cursor geschlossen")

    except Error as e:
        logger.error(f"Fehler beim Erstellen der Tabellen: {e}")
        raise


def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = False, config: Optional[Config] = None) -> Optional[List[Dict[str, Any]]]:
    logger.debug("execute_query: Aufgerufen")
    logger.debug(f"Query: {query}")
    logger.debug(f"Params: {params}")
    logger.debug(f"Fetch Mode: {fetch}")

    try:
        conn = get_connection(config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(query, params or ())
        logger.debug("execute_query: SQL ausgeführt")

        if fetch:
            result = cursor.fetchall()
            logger.debug(f"execute_query: {len(result)} Zeilen erhalten")
            return result
        else:
            conn.commit()
            logger.debug("execute_query: Änderungen committet")
            return None

    except Error as e:
        logger.error(f"Datenbankfehler bei execute_query: {e}")
        raise

    finally:
        try:
            if cursor:
                cursor.close()
                logger.debug("execute_query: Cursor geschlossen")
            if conn:
                conn.close()
                logger.debug("execute_query: Verbindung geschlossen")
        except Exception as cleanup_error:
            logger.warning(f"Fehler beim Aufräumen von Cursor/Verbindung: {cleanup_error}")
