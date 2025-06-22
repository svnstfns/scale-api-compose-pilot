# app/file_counter.py
"""
File Counter module for the VideoInventory application.
This module counts files and directories in specified filesystem sections,
tracking progress and storing results in the database.
"""

import os
import logging
import time
from typing import Optional, Dict, Tuple
from app.config import Config
from app.db_utils import execute_query


class FileCounter:
    """
    Counts files and directories in a specific section.
    """

    def __init__(self, section_path: str, logger: logging.Logger, config: Optional[Config] = None):
        """
        Initializes the FileCounter.

        Args:
            section_path: Path to the section to process
            logger: Logger instance
            config: Configuration object (optional)
        """
        self.section_path = section_path
        self.section_name = os.path.basename(section_path)
        self.logger = logger
        self.config = config or Config()

        # Initialize counters
        self.total_files = 0
        self.total_directories = 0
        self.start_time = time.time()
        self.current_directory = ""

    def run(self) -> Tuple[int, int]:
        """
        Runs the file counting for the specified section.

        Returns:
            Tuple of (file count, directory count)
        """
        self.logger.info(f"Starting file count for section: {self.section_name}")

        try:
            # Check if the section has already been counted
            if self._is_section_counted():
                # Get the existing counts
                file_count, dir_count = self._get_existing_counts()
                self.logger.info(f"Section '{self.section_name}' has already been counted. Using stored values.")
                return file_count, dir_count

            # Begin counting
            self.logger.info("Counting files and directories")
            self._mark_section_status("counting")

            # Start the count
            self._count_files()

            # Save the results to the database
            self.logger.info("Saving results")
            self._save_results()

            # Mark as counted
            self._mark_section_status("counted")

            # Final update
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))
            self.logger.info(f"Counting completed in {elapsed_str}")

            self.logger.info(f"*** Counting of '{self.section_name}' successfully completed ***\n"
                          f"Files found: {self.total_files}\n"
                          f"Directories found: {self.total_directories}")

            return self.total_files, self.total_directories

        except Exception as e:
            error_msg = f"Error during file counting for section '{self.section_name}': {str(e)}"
            self.logger.error(error_msg)

            # Mark the section as error
            self._mark_section_status("error")
            raise

    def _is_section_counted(self) -> bool:
        """
        Checks if the section has already been counted.

        Returns:
            True if the section has already been counted, otherwise False
        """
        try:
            results = execute_query(
                "SELECT status FROM section_status WHERE section_path = ?",
                (self.section_path,),
                fetch=True
            )

            # If the status is 'counted', 'indexing' or 'completed', the section has already been counted
            if results and results[0]['status'] in ['counted', 'indexing', 'completed']:
                return True

            # Check if counts exist in the file_counts table
            counts = execute_query(
                "SELECT total_files, total_directories FROM file_counts WHERE share_name = ?",
                (self.section_path,),
                fetch=True
            )

            return counts and len(counts) > 0
        except Exception as e:
            self.logger.error(f"Error checking count status for '{self.section_name}': {e}")
            return False

    def _get_existing_counts(self) -> Tuple[int, int]:
        """
        Gets the existing counts from the database.

        Returns:
            Tuple of (file count, directory count)
        """
        try:
            results = execute_query(
                "SELECT total_files, total_directories FROM file_counts WHERE share_name = ?",
                (self.section_path,),
                fetch=True
            )

            if results and len(results) > 0:
                return results[0]['total_files'], results[0]['total_directories']
            else:
                return 0, 0
        except Exception as e:
            self.logger.error(f"Error retrieving counts for '{self.section_name}': {e}")
            return 0, 0

    def _mark_section_status(self, status: str) -> None:
        """
        Updates the status of a section in the database.

        Args:
            status: New status ('counting', 'counted', 'indexing', 'completed', 'error')
        """
        try:
            # Check if entry exists
            results = execute_query(
                "SELECT 1 FROM section_status WHERE section_path = ?",
                (self.section_path,),
                fetch=True
            )

            if results:
                # Update existing entry
                execute_query(
                    """
                    UPDATE section_status 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE section_path = ?
                    """,
                    (status, self.section_path)
                )
            else:
                # Insert new entry
                execute_query(
                    """
                    INSERT INTO section_status (section_path, status, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (self.section_path, status)
                )

            self.logger.info(f"Status for section '{self.section_name}' set to '{status}'.")
        except Exception as e:
            self.logger.error(f"Error updating section status: {e}")

    def _count_files(self) -> None:
        """
        Counts files and directories in the section.
        """
        # Check if the path exists
        if not os.path.exists(self.section_path):
            self.logger.error(f"Path does not exist: {self.section_path}")
            raise FileNotFoundError(f"Path does not exist: {self.section_path}")

        # Begin counting
        for root, dirs, files in os.walk(self.section_path):
            # Update counters
            self.total_files += len(files)
            self.total_directories += len(dirs)

            # Update progress
            self.current_directory = root
            # Log periodic updates
            if self.total_files % 10000 == 0:
                self.logger.info(f"Counting progress: {self.total_files} files, {self.total_directories} directories")

    def _save_results(self) -> None:
        """
        Saves the count results to the database.
        """
        try:
            # Check if entry exists
            results = execute_query(
                "SELECT 1 FROM file_counts WHERE share_name = ?",
                (self.section_path,),
                fetch=True
            )

            if results:
                # Update existing entry
                execute_query(
                    """
                    UPDATE file_counts 
                    SET total_files = ?, total_directories = ?, created_at = CURRENT_TIMESTAMP
                    WHERE share_name = ?
                    """,
                    (self.total_files, self.total_directories, self.section_path)
                )
            else:
                # Insert new entry
                execute_query(
                    """
                    INSERT INTO file_counts (share_name, total_files, total_directories)
                    VALUES (?, ?, ?)
                    """,
                    (self.section_path, self.total_files, self.total_directories)
                )

            self.logger.info(f"Count results for section '{self.section_name}' saved: "
                          f"{self.total_files} files, {self.total_directories} directories.")
        except Exception as e:
            self.logger.error(f"Error saving count results: {e}")
            raise