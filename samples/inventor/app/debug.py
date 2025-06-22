#!/usr/bin/env python3
# debug.py - Script to debug database connection and application state

import os
import sys
import time
import logging
from app.logger import setup_logger
from app.config import Config
from app.database_utils import wait_for_database, ensure_tables_exist, execute_query

# Set up logging
logger = setup_logger("debug", "/app/logs")


def main():
    """
    Debugging function to check system status
    """
    logger.info("=== Debug Script Running ===")

    try:
        # Load configuration
        config = Config()
        logger.info("Configuration loaded")

        # Print key configuration values
        logger.info(f"Database config: {config.db_config}")
        logger.info(f"Base directories: {config.base_directories}")

        # Check database connection
        logger.info("Testing database connection...")
        wait_for_database(logger, config)
        logger.info("Database connection successful")

        # Check tables
        logger.info("Checking database tables...")
        ensure_tables_exist(logger, config)
        logger.info("Database tables checked")

        # Check available directories
        logger.info("Checking base directories...")
        for directory in config.base_directories:
            if os.path.exists(directory):
                logger.info(f"  - {directory}: EXISTS")
            else:
                logger.warning(f"  - {directory}: MISSING")

        # Check section status
        logger.info("Checking section status...")
        sections = execute_query("SELECT * FROM section_status", fetch=True)
        logger.info(f"Found {len(sections) if sections else 0} sections in database")

        # Check file counts
        logger.info("Checking file counts...")
        counts = execute_query("SELECT * FROM file_counts", fetch=True)
        logger.info(f"Found {len(counts) if counts else 0} file count records")

        # Check inventory
        logger.info("Checking inventory...")
        inventory = execute_query("SELECT COUNT(*) as count FROM inventory", fetch=True)
        if inventory:
            logger.info(f"Inventory has {inventory[0]['count']} records")

        logger.info("=== Debug Complete ===")

    except Exception as e:
        logger.error(f"Error during debugging: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())