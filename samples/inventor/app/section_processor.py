# app/section_processor.py
import os
import logging
import threading
import time
from typing import List, Dict, Optional
from app.file_counter import FileCounter
from app.file_indexer import FileIndexer
from app.config import Config
from app.section_discovery import discover_sections


class SectionProcessor:
    """
    Processes multiple sections in parallel with multithreading.
    Uses logging for status updates.
    """

    def __init__(self, sections: List[str] = None, logger: logging.Logger = None, config: Config = None):
        """
        Initializes the SectionProcessor.

        Args:
            sections: List of section paths (optional)
            logger: Logger instance
            config: Configuration object (optional)
        """
        self.config = config or Config()
        self.logger = logger or logging.getLogger(__name__)

        if sections:
            self.sections = sections
        else:
            # Use section_discovery if no sections were provided
            self.sections = discover_sections(self.config.base_directories, self.config.max_section_depth, self.logger)

        self.threads = []
        self.section_status: Dict[str, str] = {}
        self.start_time = time.time()
        self.active_threads = 0
        self.lock = threading.Lock()
        self.processing_complete = False

        # Initialize status tracking for each section
        for section in self.sections:
            section_name = os.path.basename(section)
            self.section_status[section] = "Pending"

    def start(self):
        """
        Starts processing all sections with multithreading.
        """
        self.logger.info(f"Starting processing of {len(self.sections)} sections")
        self.logger.info("Starting thread pool")

        try:
            # Create a thread pool with a limited number of concurrent threads
            self._process_sections_with_pool()

            # Show final statistics
            completed = sum(1 for status in self.section_status.values() if status == "Completed")
            failed = sum(1 for status in self.section_status.values() if status == "Error")

            elapsed_time = time.time() - self.start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

            self.logger.info(f"Processing of {len(self.sections)} sections completed")
            self.logger.info(f"Successful: {completed}")
            self.logger.info(f"Failed: {failed}")
            self.logger.info(f"Total time: {elapsed_str}")

        except Exception as e:
            self.logger.error(f"Error during section processing: {e}")
            raise

    def _process_sections_with_pool(self):
        """
        Processes sections with a thread pool of limited size.
        """
        sections_queue = list(self.sections)  # Copy of the list for processing
        max_threads = self.config.thread_count
        active_threads = []

        self.logger.info(f"Processing with maximum {max_threads} threads")

        while sections_queue or active_threads:
            # Remove completed threads
            for thread in list(active_threads):
                if not thread.is_alive():
                    active_threads.remove(thread)

            # Update status tracking
            with self.lock:
                self.active_threads = len(active_threads)
                completed = sum(1 for status in self.section_status.values() if status == "Completed")
                in_progress = sum(1 for status in self.section_status.values() if status == "In Progress")
                pending = sum(1 for status in self.section_status.values() if status == "Pending")
                failed = sum(1 for status in self.section_status.values() if status == "Error")

                elapsed_time = time.time() - self.start_time
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

                # Log status periodically
                if len(sections_queue) % 5 == 0 or len(sections_queue) < 5:
                    self.logger.info(f"Progress: {completed}/{len(self.sections)} sections completed in {elapsed_str}")
                    self.logger.info(f"Active threads: {self.active_threads}, Pending sections: {len(sections_queue)}")

            # Start new threads if there's room and sections are available
            while len(active_threads) < max_threads and sections_queue:
                section = sections_queue.pop(0)
                thread = threading.Thread(target=self._process_section, args=(section,))
                thread.start()
                active_threads.append(thread)

                # Short pause to prevent all threads from starting simultaneously
                time.sleep(0.1)

            # Short pause before the next check
            time.sleep(0.5)

        self.logger.info("All section threads completed")

    def _process_section(self, section_path: str):
        """
        Processes a single section.

        Args:
            section_path: Path to the section
        """
        section_name = os.path.basename(section_path)

        with self.lock:
            self.section_status[section_path] = "In Progress"

        self.logger.info(f"Starting processing of section: {section_name}")

        try:
            # 1. Count files and directories
            counter = FileCounter(section_path, self.logger, self.config)
            counter.run()

            # 2. Index the files
            indexer = FileIndexer(section_path, self.logger, self.config)
            indexer.run()

            with self.lock:
                self.section_status[section_path] = "Completed"

            self.logger.info(f"Section '{section_name}' successfully processed")
        except Exception as e:
            with self.lock:
                self.section_status[section_path] = "Error"
            self.logger.error(f"Error processing section '{section_name}': {str(e)}")

    def get_status_summary(self) -> Dict[str, int]:
        """
        Returns a summary of the current processing status.

        Returns:
            Dict with status counts
        """
        with self.lock:
            return {
                "total": len(self.sections),
                "completed": sum(1 for status in self.section_status.values() if status == "Completed"),
                "in_progress": sum(1 for status in self.section_status.values() if status == "In Progress"),
                "pending": sum(1 for status in self.section_status.values() if status == "Pending"),
                "failed": sum(1 for status in self.section_status.values() if status == "Error")
            }