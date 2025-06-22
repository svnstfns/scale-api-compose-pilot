#!/usr/bin/env python3
# debug_scan.py - Script to debug directory scanning and section discovery

import os
import sys
import logging
from app.logger import setup_logger
from app.config import Config
from app.section_discovery import discover_sections, filter_sections

# Set up logging
logger = setup_logger("debug_scan", "/app/logs", logging.DEBUG, debug=True)


def main():
    """
    Debugging function to test directory scanning
    """
    logger.info("=== Directory Scanning Debug Script Running ===")

    try:
        # Load configuration
        config = Config()
        logger.info(f"Configuration loaded with {len(config.base_directories)} base directories")

        # Print base directories
        for i, directory in enumerate(config.base_directories):
            exists = os.path.exists(directory)
            is_dir = os.path.isdir(directory) if exists else False
            readable = os.access(directory, os.R_OK) if exists else False

            logger.info(f"Base directory {i + 1}: {directory}")
            logger.info(f"  - Exists: {exists}")
            logger.info(f"  - Is directory: {is_dir}")
            logger.info(f"  - Readable: {readable}")

            if exists and is_dir:
                try:
                    items = os.listdir(directory)
                    logger.info(f"  - Contains {len(items)} items")
                    if items:
                        logger.info(f"  - First few items: {', '.join(items[:5])}")
                except Exception as e:
                    logger.error(f"  - Error listing directory: {e}")

        # Test section discovery with first directory
        if config.base_directories:
            first_dir = config.base_directories[0]
            logger.info(f"Testing section discovery with first directory: {first_dir}")

            # Try with depth of 1 first
            try:
                logger.info("Discovering sections with depth=1...")
                sections = discover_sections([first_dir], 1, logger)
                logger.info(f"Found {len(sections)} sections with depth 1")
                for i, section in enumerate(sections[:10]):  # Print first 10
                    logger.info(f"  - Section {i + 1}: {section}")
            except Exception as e:
                logger.error(f"Error during section discovery (depth=1): {e}", exc_info=True)

            # Try with configured depth
            max_depth = config.max_section_depth
            try:
                logger.info(f"Discovering sections with depth={max_depth}...")
                sections = discover_sections([first_dir], max_depth, logger)
                logger.info(f"Found {len(sections)} sections with depth {max_depth}")
                for i, section in enumerate(sections[:10]):  # Print first 10
                    logger.info(f"  - Section {i + 1}: {section}")
            except Exception as e:
                logger.error(f"Error during section discovery (depth={max_depth}): {e}", exc_info=True)
        else:
            logger.error("No base directories defined, cannot test section discovery")

        logger.info("=== Directory Scanning Debug Complete ===")

    except Exception as e:
        logger.error(f"Error during debug scan: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())