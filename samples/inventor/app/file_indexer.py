# app/file_indexer.py
"""
File Indexer module for the VideoInventory application.
This module is responsible for indexing files in filesystem sections with a focus on video files,
extracting metadata, and storing information in the database.
"""

import os
import mimetypes
import logging
import time
from typing import Optional, Dict, List
from app.config import Config
from app.db_utils import execute_query, get_connection
from app.utils import human_readable_size, is_video_file, is_mp4_file
from app.video_metadata import VideoMetadata
from app.file_id_generator import FileIDGenerator


class FileIndexer:
    """
    Indexes files in a specific section with a focus on video files.
    """

    def __init__(self, section_path: str, logger: logging.Logger, config: Optional[Config] = None, main_display=None):
        """
        Initializes the FileIndexer.

        Args:
            section_path: Path to the section to process
            logger: Logger instance
            config: Configuration object (optional)
            main_display: Main display object (optional)
        """
        self.section_path = section_path
        self.section_name = os.path.basename(section_path)
        self.logger = logger
        self.config = config or Config()
        self.conn = None
        self.main_display = main_display

        # Initialize counters for display
        self.total_files = 0
        self.processed_files = 0
        self.mp4_files = 0
        self.non_mp4_videos = 0
        self.error_count = 0
        self.start_time = time.time()

        # Statistics for indexed files
        self.indexed_files = 0
        self.updated_files = 0
        self.skipped_files = 0
        self.queued_for_conversion = 0

    def run(self) -> None:
        """
        Runs the indexing for the specified section.
        """
        self.logger.info(f"Starting indexing for section: {self.section_name}")

        try:
            # Check if the section has already been indexed
            if self._is_section_indexed():
                self.logger.info(f"Section '{self.section_name}' has already been indexed. Skipping...")
                return

            # Get the number of files
            self.total_files = self._get_total_files()
            self.logger.info(f"Found {self.total_files} files to process")

            if self.total_files > 0:
                # Mark the section as 'indexing'
                self._mark_section_status("indexing")

                # Establish database connection
                self.conn = get_connection()

                # Process the files
                self.logger.info(f"Processing files in section: {self.section_name}")
                self._process_files()

                # Update the section status
                self.logger.info("Finalizing")
                self._mark_section_as_indexed()

                # Final update
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))

                self.logger.info(f"*** Indexing of '{self.section_name}' successfully completed ***\n"
                                 f"Processed files: {self.processed_files}\n"
                                 f"MP4 files: {self.mp4_files}\n"
                                 f"Other videos: {self.non_mp4_videos}\n"
                                 f"Newly indexed: {self.indexed_files}\n"
                                 f"Updated: {self.updated_files}\n"
                                 f"Skipped: {self.skipped_files}\n"
                                 f"Queued for conversion: {self.queued_for_conversion}\n"
                                 f"Errors: {self.error_count}")
            else:
                self.logger.warning(f"No files found to index in section: {self.section_name}")

        except Exception as e:
            error_msg = f"Error during indexing of section '{self.section_name}': {str(e)}"
            self.logger.error(error_msg)

            # Mark the section as error
            self._mark_section_status("error")
            raise

    def _is_section_indexed(self) -> bool:
        """
        Checks if the section has already been indexed.

        Returns:
            True if the section has already been indexed, otherwise False
        """
        try:
            results = execute_query(
                "SELECT status FROM section_status WHERE section_path = ?",
                (self.section_path,),
                fetch=True
            )

            return results and results[0]['status'] == 'completed'
        except Exception as e:
            self.logger.error(f"Error checking indexing status for '{self.section_name}': {e}")
            return False

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

    def _get_total_files(self) -> int:
        """
        Gets the total number of files in the section from the database.

        Returns:
            Number of files in the section
        """
        try:
            results = execute_query(
                "SELECT total_files FROM file_counts WHERE share_name = ?",
                (self.section_path,),
                fetch=True
            )

            if results and results[0]['total_files'] is not None:
                return results[0]['total_files']
            else:
                self.logger.warning(f"No file count found for section '{self.section_name}'.")
                self.logger.info("Counting files directly")
                return self._count_files_directly()
        except Exception as e:
            self.logger.error(f"Error retrieving file count for '{self.section_name}': {e}")
            self.logger.info("Counting files directly")
            return self._count_files_directly()

    def _count_files_directly(self) -> int:
        """
        Counts the files directly if no count is available in the database.

        Returns:
            Number of files in the section
        """
        self.logger.info(f"Counting files directly in section '{self.section_name}'...")
        count = 0
        for root, _, files in os.walk(self.section_path):
            file_count = len(files)
            count += file_count
            if count % 10000 == 0:
                self.logger.info(f"Counting... {count} files found so far")

        return count

    def _process_files(self) -> None:
        """
        Processes all files in the section.
        Uses log updates for progress tracking.
        """
        progress_interval = max(1, min(10000, self.total_files // 20))  # Log progress at reasonable intervals

        for root, _, files in os.walk(self.section_path):
            for file in files:
                file_path = os.path.join(root, file)
                self.processed_files += 1

                # Calculate and update progress periodically
                if self.processed_files % progress_interval == 0:
                    elapsed = time.time() - self.start_time
                    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
                    percent = int((self.processed_files / self.total_files) * 100) if self.total_files > 0 else 0

                    self.logger.info(
                        f"Progress: {self.processed_files}/{self.total_files} files ({percent}%) in {elapsed_str}")
                    self.logger.info(
                        f"MP4 files: {self.mp4_files}, Other videos: {self.non_mp4_videos}, Errors: {self.error_count}")

                try:
                    self._process_file(file_path)
                except Exception as e:
                    self.error_count += 1
                    self.logger.error(f"Error processing '{file_path}': {e}")
                    self._record_error(file_path, str(e))

    def _process_file(self, file_path: str) -> None:
        """
        Processes a single file.

        Args:
            file_path: Path to the file
        """
        # First check if it's a video file
        if not is_video_file(file_path):
            self.skipped_files += 1
            return

        # Basic file properties
        filename = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)

        try:
            file_size = os.path.getsize(file_path)
            file_size_hr = human_readable_size(file_size)
        except OSError as e:
            self.logger.error(f"Error reading file size of '{file_path}': {e}")
            self.error_count += 1
            self._record_error(file_path, f"Error reading file size: {e}")
            return

        # Process based on file type
        if is_mp4_file(file_path):
            self.mp4_files += 1
            self._process_mp4_file(file_path, filename, mime_type, file_size, file_size_hr)
        else:
            self.non_mp4_videos += 1
            self._add_to_conversion_queue(file_path)

    def _process_mp4_file(self, file_path: str, filename: str, mime_type: str,
                          file_size: int, file_size_hr: str) -> None:
        """
        Processes an MP4 file.

        Args:
            file_path: Path to the file
            filename: Name of the file
            mime_type: MIME type of the file
            file_size: Size of the file in bytes
            file_size_hr: Human readable file size
        """
        try:
            metadata = VideoMetadata(file_path, self.logger)
            file_id = metadata.get_metadata('pnxid')

            if file_id:
                self.logger.info(f"File ID found in metadata: {file_id}, updating file: {file_path}")
                self._update_inventory(file_id, file_path, filename, mime_type, file_size, file_size_hr)
                self.updated_files += 1
            else:
                # Generate a new file ID
                generator = FileIDGenerator(file_path)
                new_file_id = generator.generate_file_id()

                # Save it to metadata
                if metadata.add_metadata('pnxid', new_file_id):
                    self.logger.info(
                        f"New file ID '{new_file_id}' generated and saved in metadata for: {file_path}")
                else:
                    self.logger.warning(
                        f"Could not update metadata, still using ID '{new_file_id}' for: {file_path}")

                # Insert into inventory table
                self._insert_into_inventory(new_file_id, file_path, filename, mime_type, file_size, file_size_hr)
                self.indexed_files += 1
        except Exception as e:
            self.logger.error(f"Error processing MP4 file '{file_path}': {e}")
            self._record_error(file_path, str(e))
            self.error_count += 1

    def _add_to_conversion_queue(self, file_path: str) -> None:
        """
        Adds a file to the conversion queue.

        Args:
            file_path: Path to the source file
        """
        target_path = os.path.splitext(file_path)[0] + ".mp4"
        self.logger.info(f"Non-MP4 video file found: {file_path}, adding to conversion queue.")

        try:
            # Check if entry exists
            results = execute_query(
                "SELECT 1 FROM conversion_queue WHERE filepath = ?",
                (file_path,),
                fetch=True
            )

            if results:
                # Update existing entry
                execute_query(
                    """
                    UPDATE conversion_queue
                    SET target_path = ?, status = 'pending'
                    WHERE filepath = ?
                    """,
                    (target_path, file_path)
                )
            else:
                # Insert new entry
                execute_query(
                    """
                    INSERT INTO conversion_queue (filepath, target_path, status)
                    VALUES (?, ?, 'pending')
                    """,
                    (file_path, target_path)
                )

            self.queued_for_conversion += 1
        except Exception as e:
            self.logger.error(f"Error adding to conversion queue: {e}")
            self.error_count += 1

    def _insert_into_inventory(self, file_id: str, filepath: str, filename: str,
                               mimetype: str, size: int, size_hr: str) -> None:
        """
        Inserts a record into the inventory table.

        Args:
            file_id: Unique file ID
            filepath: Full path to the file
            filename: Name of the file
            mimetype: MIME type of the file
            size: Size of the file in bytes
            size_hr: Human readable file size
        """
        try:
            # Check if entry exists
            results = execute_query(
                "SELECT 1 FROM inventory WHERE file_id = ?",
                (file_id,),
                fetch=True
            )

            if results:
                # Update existing entry
                execute_query(
                    """
                    UPDATE inventory SET
                        filepath = ?,
                        filename = ?,
                        mimetype = ?,
                        size = ?,
                        size_hr = ?,
                        status = 'updated'
                    WHERE file_id = ?
                    """,
                    (filepath, filename, mimetype, size, size_hr, file_id)
                )
            else:
                # Insert new entry
                execute_query(
                    """
                    INSERT INTO inventory 
                    (file_id, filepath, filename, mimetype, size, size_hr, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'new')
                    """,
                    (file_id, filepath, filename, mimetype, size, size_hr)
                )

            self.logger.info(f"File '{filename}' inserted into inventory.")
        except Exception as e:
            self.logger.error(f"Error inserting into inventory: {e}")
            self.error_count += 1

    def _update_inventory(self, file_id: str, filepath: str, filename: str,
                          mimetype: str, size: int, size_hr: str) -> None:
        """
        Updates an existing record in the inventory table.

        Args:
            file_id: Unique file ID
            filepath: Full path to the file
            filename: Name of the file
            mimetype: MIME type of the file
            size: Size of the file in bytes
            size_hr: Human readable file size
        """
        try:
            execute_query(
                """
                UPDATE inventory SET
                    filepath = ?,
                    filename = ?,
                    mimetype = ?,
                    size = ?,
                    size_hr = ?,
                    status = 'updated'
                WHERE file_id = ?
                """,
                (filepath, filename, mimetype, size, size_hr, file_id)
            )
            self.logger.info(f"File '{filename}' updated in inventory.")
        except Exception as e:
            self.logger.error(f"Error updating inventory: {e}")
            self.error_count += 1

    def _record_error(self, file_path: str, error_message: str) -> None:
        """
        Records an error in the error_log table.

        Args:
            file_path: Path to the file that caused the error
            error_message: Error message
        """
        filename = os.path.basename(file_path)

        try:
            # Check if entry exists
            results = execute_query(
                "SELECT 1 FROM error_log WHERE file_path = ?",
                (file_path,),
                fetch=True
            )

            if results:
                # Update existing entry
                execute_query(
                    """
                    UPDATE error_log
                    SET issue = ?, timestamp = CURRENT_TIMESTAMP
                    WHERE file_path = ?
                    """,
                    (error_message, file_path)
                )
            else:
                # Insert new entry
                execute_query(
                    """
                    INSERT INTO error_log (file_path, file_name, issue)
                    VALUES (?, ?, ?)
                    """,
                    (file_path, filename, error_message)
                )

        except Exception as e:
            self.logger.error(f"Error recording error: {e}")

    def _mark_section_as_indexed(self) -> None:
        """
        Marks the section as indexed in the database.
        """
        self._mark_section_status("completed")