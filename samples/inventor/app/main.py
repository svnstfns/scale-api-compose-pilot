#!/usr/bin/env python3
"""
Main module for the VideoInventory application.
This is the entry point that coordinates mounting directories,
discovering sections, and processing video files.
"""

import os
import argparse
import atexit
import time
import threading
import sys
import traceback
import logging
from app.logger import setup_logger
from app.config import Config
from app.db_utils import initialize_database, execute_query, close_connections
from app.section_discovery import discover_sections, filter_sections
from app.webservice import start_server

BASE_MOUNT_DIR = "/Users/sst/PycharmProjects/videoinventor/mountpoints"


def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description='VideoInventory - Inventory system for video files')

    parser.add_argument('--discover-only', action='store_true',
                        help='Only discover sections, do not process them')

    parser.add_argument('--include', action='append',
                        help='Only include sections matching these patterns (can be used multiple times)')

    parser.add_argument('--exclude', action='append',
                        help='Exclude sections matching these patterns (can be used multiple times)')

    parser.add_argument('--max-depth', type=int, default=2,
                        help='Maximum directory depth for section discovery (default: 2)')

    parser.add_argument('--threads', type=int, default=2,
                        help='Number of threads for parallel processing (default: 2)')

    parser.add_argument('--db-path', type=str,
                        help='Path to SQLite database file')

    parser.add_argument('--timeout', type=int, default=300,
                        help='Timeout in seconds for long operations (default: 300)')

    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode with more verbose logging')

    parser.add_argument('--skip-nfs', action='store_true',
                        help='Skip NFS mounting and use local directories')

    return parser.parse_args()


def show_welcome():
    """Displays a welcome message."""
    print("\n" + "=" * 80)
    print(" VideoInventory - Video File Inventory System ".center(80, "="))
    print("=" * 80 + "\n")


def watchdog_timer(timeout, operation_name):
    """
    Creates a watchdog timer that will print diagnostic info if an operation takes too long.

    Args:
        timeout: Timeout in seconds
        operation_name: Name of the operation being monitored
    """
    start_time = time.time()

    def check_timeout():
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"\n*** WATCHDOG: Operation '{operation_name}' is taking too long ({elapsed:.1f} seconds)")
            print("*** Current thread stacks:")
            for thread_id, frame in sys._current_frames().items():
                print(f"\nThread {thread_id}:")
                traceback.print_stack(frame)
                print()

            print("\n*** Watchdog will check again in 60 seconds...")
            # Schedule next check
            timer = threading.Timer(60, check_timeout)
            timer.daemon = True
            timer.start()

    # Start the initial timer
    timer = threading.Timer(timeout, check_timeout)
    timer.daemon = True
    timer.start()
    return timer


def discover_with_fallback(data_dirs, max_depth, logger, timeout, include_patterns=None, exclude_patterns=None):
    """
    Discover sections with fallback mechanisms in case of timeout or errors.

    Args:
        data_dirs: List of directories to scan
        max_depth: Maximum depth for directory traversal
        logger: Logger instance
        timeout: Timeout in seconds for the operation
        include_patterns: Optional patterns to include
        exclude_patterns: Optional patterns to exclude

    Returns:
        List of discovered sections
    """
    all_sections = []

    # Try with the requested depth first
    logger.info(f"Attempting discovery with max_depth={max_depth}")
    discovery_timer = watchdog_timer(timeout, f"Section discovery (depth={max_depth})")

    try:
        for data_dir in data_dirs:
            logger.info(f"Scanning {data_dir} with maximum depth {max_depth}")
            sections = discover_sections([data_dir], max_depth, logger)
            logger.info(f"Discovered {len(sections)} sections in {data_dir}")
            all_sections.extend(sections)
    except Exception as e:
        logger.error(f"Error during section discovery: {e}")
        logger.error(traceback.format_exc())
    finally:
        discovery_timer.cancel()

    # If we found sections, great! If not, try with a reduced depth
    if not all_sections and max_depth > 1:
        fallback_depth = 1
        logger.warning(f"No sections found with depth {max_depth}. Falling back to depth {fallback_depth}")

        fallback_timer = watchdog_timer(timeout // 2, f"Section discovery fallback (depth={fallback_depth})")
        try:
            for data_dir in data_dirs:
                logger.info(f"Fallback: Scanning {data_dir} with maximum depth {fallback_depth}")
                sections = discover_sections([data_dir], fallback_depth, logger)
                logger.info(f"Discovered {len(sections)} sections in {data_dir}")
                all_sections.extend(sections)
        except Exception as e:
            logger.error(f"Error during fallback section discovery: {e}")
            logger.error(traceback.format_exc())
        finally:
            fallback_timer.cancel()

    # Apply filters if provided
    if all_sections and (include_patterns or exclude_patterns):
        logger.info("Applying include/exclude filters...")
        original_count = len(all_sections)
        all_sections = filter_sections(all_sections, include_patterns, exclude_patterns)
        logger.info(f"Filtered sections: {original_count} -> {len(all_sections)}")

    return all_sections


def main():
    """Main application logic."""
    # Show welcome message
    show_welcome()

    # Parse arguments
    args = parse_arguments()

    # Set database path from args if provided
    if args.db_path:
        os.environ['DB_PATH'] = args.db_path

    # Set up logging and configuration
    log_level = logging.DEBUG if args.debug else logging.INFO
    config = Config()
    logger = setup_logger("main", config.log_dir, log_level)
    logger.info("VideoInventory is starting...")

    # Register cleanup function
    atexit.register(close_connections)

    # Initialize data_dirs list using directly mounted directories
    data_dirs = [
        "/Volumes/gstf-ng-video2",
        "/Volumes/gstf-ng-video",
        "/Volumes/gstf-ng-video3",
        "/Volumes/gaystuff-inbox",
        "/Volumes/gaystuff-misc"
    ]

    # Filter out non-existent directories
    valid_data_dirs = []
    for dir_path in data_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            valid_data_dirs.append(dir_path)
            logger.info(f"Using directory: {dir_path}")
        else:
            logger.warning(f"Directory does not exist: {dir_path}")

    if not valid_data_dirs:
        logger.error("No valid directories found. Exiting application.")
        return

    # Set DATA_DIRS environment variable for other modules to use
    os.environ['DATA_DIRS'] = ','.join(valid_data_dirs)

    logger.info(f"Starting database initialization...")

    # Initialize the database with watchdog
    db_timer = watchdog_timer(30, "Database initialization")
    try:
        if not initialize_database(config):
            logger.error("Failed to initialize database. Exiting application.")
            return
        logger.info("Database initialization completed.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        logger.error(traceback.format_exc())
        return
    finally:
        db_timer.cancel()

    logger.info(f"Starting webservice...")
    start_server()


    # Step 1: Discover all sections with improved handling
    logger.info("Discovering directory structure...")
    all_sections = discover_with_fallback(
        valid_data_dirs,
        args.max_depth,
        logger,
        args.timeout,
        args.include,
        args.exclude
    )

    if not all_sections:
        logger.warning("No sections found. Exiting the application.")
        return

    logger.info(f"Total sections discovered: {len(all_sections)}")

    if args.discover_only:
        print("\nDiscovered sections:")
        for section in all_sections:
            print(f" - {section}")
        return

    # Step 3: Store sections in the database
    logger.info("Storing sections in the database...")
    for section in all_sections:
        query = "INSERT OR IGNORE INTO sections (path) VALUES (?)"
        execute_query(query, (section,))
    logger.info("All sections have been stored in the database.")

    # Step 4: Process sections using a simplified approach
    logger.info("Processing sections...")
    processing_timer = watchdog_timer(args.timeout * 2, "Section processing")

    try:
        # Create a simplified section processor class that doesn't use StatusDisplay
        # For now, just process each section sequentially to avoid any potential issues
        process_sections_sequentially(all_sections, logger, config)
    except Exception as e:
        logger.error(f"Error during section processing: {e}")
        logger.error(traceback.format_exc())
    finally:
        processing_timer.cancel()

    logger.info("Section processing completed. Exiting application.")


def process_sections_sequentially(sections, logger, config):
    """
    Process each section sequentially to avoid any Status Display dependencies.

    Args:
        sections: List of sections to process
        logger: Logger instance
        config: Configuration object
    """
    from app.file_counter import FileCounter
    from app.file_indexer import FileIndexer

    logger.info(f"Starting sequential processing of {len(sections)} sections")

    for i, section_path in enumerate(sections, 1):
        section_name = os.path.basename(section_path)
        logger.info(f"Processing section {i}/{len(sections)}: {section_name}")

        try:
            # 1. Count files and directories in the section
            logger.info(f"Counting files in {section_path}")
            counter = FileCounter(section_path, logger, config)
            counter.run()

            # 2. Index files in the section
            logger.info(f"Indexing files in {section_path}")
            indexer = FileIndexer(section_path, logger, config)
            indexer.run()

            logger.info(f"Completed processing section: {section_name}")

        except Exception as e:
            logger.error(f"Error processing section {section_name}: {e}")
            logger.error(traceback.format_exc())
            # Continue with next section


if __name__ == "__main__":
    main()