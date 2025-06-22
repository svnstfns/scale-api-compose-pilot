# app/config.py
import os
import platform
from typing import List, Dict, Any
import logging


class Config:
    """Central configuration class for the VideoInventory application."""

    def __init__(self):
        # Set up logger
        self.logger = logging.getLogger(__name__)

        # Database configuration - SQLite
        db_path = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'videoinventory.db'))
        self.logger.info(f"Using SQLite database at: {db_path}")

        self.db_config = {
            'database': db_path
        }

        # Get DATA_DIRS environment variable
        data_dirs_env = os.getenv('DATA_DIRS', '/Volumes/gaystuff-video,/Volumes/gaystuff-inbox,/Volumes/gaystuff-misc,/Volumes/gstf-ng-video,/Volumes/gstf-ng-video2,/Volumes/gstf-ng-video3')
        self.logger.info(f"DATA_DIRS environment variable: {data_dirs_env}")

        # Path settings
        # Parse the comma-separated list from environment, handling whitespace properly
        data_dir_list = [path.strip() for path in data_dirs_env.split(',') if path.strip()]
        self.logger.info(f"Parsed {len(data_dir_list)} directories from DATA_DIRS")

        # Normalize each path - handle both local macOS paths and server paths
        self.base_directories = []
        for path in data_dir_list:
            norm_path = self.normalize_path(path)
            self.base_directories.append(norm_path)
            self.logger.info(f"Added base directory: {norm_path} (original: {path})")

        if not self.base_directories:
            self.logger.warning("No base directories found! Using default /Volumes")
            self.base_directories = ["/Volumes"]

        self.log_dir = os.getenv('LOG_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs'))
        os.makedirs(self.log_dir, exist_ok=True)

        # Application settings
        self.max_section_depth = int(os.getenv('MAX_SECTION_DEPTH', 4))
        self.thread_count = int(os.getenv('THREAD_COUNT', 4))

    def normalize_path(self, path: str) -> str:
        """
        Normalize a path for the current platform.

        Args:
            path: Original path

        Returns:
            Normalized path
        """
        # Convert to absolute path
        abs_path = os.path.abspath(path)

        # Normalize path separators
        norm_path = os.path.normpath(abs_path)

        return norm_path

    def adjust_path(self, path: str) -> str:
        """
        Adjust paths for the current platform if needed.

        Args:
            path: Original path

        Returns:
            Adjusted path for current platform
        """
        return path  # Default implementation just returns the path as is

    def get_required_tables(self) -> Dict[str, str]:
        """
        Returns the SQL statements needed to create required database tables.

        Returns:
            Dictionary of table names to their creation SQL statements
        """
        return {
            "section_status": """
                CREATE TABLE IF NOT EXISTS section_status (
                    section_path TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "file_counts": """
                CREATE TABLE IF NOT EXISTS file_counts (
                    share_name TEXT PRIMARY KEY,
                    total_files INTEGER,
                    total_directories INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "inventory": """
                CREATE TABLE IF NOT EXISTS inventory (
                    file_id TEXT PRIMARY KEY,
                    filepath TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    mimetype TEXT,
                    size INTEGER,
                    size_hr TEXT,
                    checksum TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filepath)
                )
            """,
            "error_log": """
                CREATE TABLE IF NOT EXISTS error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    issue TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_path)
                )
            """,
            "conversion_queue": """
                CREATE TABLE IF NOT EXISTS conversion_queue (
                    filepath TEXT PRIMARY KEY,
                    target_path TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "duplicates": """
                CREATE TABLE IF NOT EXISTS duplicates (
                    checksum TEXT PRIMARY KEY,
                    duplicate_count INTEGER DEFAULT 0
                )
            """,
            "video_properties": """
                CREATE TABLE IF NOT EXISTS video_properties (
                    file_path TEXT NOT NULL,
                    checksum TEXT PRIMARY KEY,
                    codec_name TEXT,
                    resolution TEXT,
                    quality TEXT,
                    duration TEXT,
                    result TEXT
                )
            """,
            "sections": """
                CREATE TABLE IF NOT EXISTS sections (
                    path TEXT PRIMARY KEY
                )
            """
        }