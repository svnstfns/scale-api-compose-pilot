# app/find_duplicates.py
"""
Find Duplicates module for the VideoInventory application.
This module identifies duplicate video files in the inventory
based on their checksums and updates a duplicates table.
"""

import os
import logging
from app.db_utils import execute_query
from app.logger import setup_logger

# Get the logger instance
logger = setup_logger("find_duplicates")


def calc_duplicates():
    """
    Calculates duplicates in the inventory based on checksums.
    Inserts results into the duplicates table.
    """
    logger.info("calculating duplicates...")

    try:
        # Query to identify files with the same checksums
        execute_query("""
            INSERT OR IGNORE INTO duplicates (checksum, duplicate_count)
            SELECT checksum, COUNT(*) - 1
            FROM inventory
            WHERE checksum IS NOT NULL
            GROUP BY checksum
            HAVING COUNT(*) > 1
        """)

        logger.info("calculating duplicates -> done!")
    except Exception as e:
        logger.error(f"Error calculating duplicates: {e}")


if __name__ == "__main__":
    calc_duplicates()
    print("***FIN***")