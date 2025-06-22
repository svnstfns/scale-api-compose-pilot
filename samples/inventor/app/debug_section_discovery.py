# debug_section_discovery.py
import os
import logging
from app.logger import setup_logger
from app.config import Config
from app.section_discovery import discover_sections

# Set up logging
logger = setup_logger("debug_sections", "./logs", logging.DEBUG, debug=True)


def main():
    # Create a test directory structure if it doesn't exist
    test_base = "./test_data"
    os.makedirs(f"{test_base}/dir1/subdir1", exist_ok=True)
    os.makedirs(f"{test_base}/dir2/subdir2", exist_ok=True)

    # Create some test files
    open(f"{test_base}/dir1/test1.txt", "w").close()
    open(f"{test_base}/dir1/subdir1/test2.txt", "w").close()

    # Override environment variable
    os.environ["DATA_DIRS"] = test_base

    # Load configuration
    config = Config()
    logger.info(f"Base directories: {config.base_directories}")

    # Try discovering sections
    logger.info("Starting section discovery...")
    try:
        sections = discover_sections(config.base_directories, 2, logger)
        logger.info(f"Discovered {len(sections)} sections:")
        for section in sections:
            logger.info(f"  - {section}")
    except Exception as e:
        logger.error(f"Error in section discovery: {e}", exc_info=True)


if __name__ == "__main__":
    main()
