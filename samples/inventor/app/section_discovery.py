# app/section_discovery.py
"""
Section Discovery module for the VideoInventory application.
This module finds and categorizes filesystem sections that need to be processed,
allowing for filtering and depth-limited traversal.
"""

import os
import sys
import traceback
import time
from typing import List, Optional, Set
import logging
from app.config import Config


def discover_sections(base_dirs: List[str], max_depth: int = 4, logger: Optional[logging.Logger] = None) -> List[str]:
    """
    Discovers directory sections up to the specified maximum depth.

    Args:
        base_dirs: List of base directories to search
        max_depth: Maximum directory depth
        logger: Logger instance (optional)

    Returns:
        List of discovered section paths
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    config = Config()
    sections: Set[str] = set()

    # Log all base directories for debugging
    logger.info(f"Starting section discovery with {len(base_dirs)} base directories:")
    for i, base_dir in enumerate(base_dirs):
        logger.info(f"  {i + 1}. {base_dir}")

    # Check each base directory
    for i, base_dir in enumerate(base_dirs, 1):
        if not base_dir or not base_dir.strip():
            logger.warning(f"Empty base directory at index {i}, skipping")
            continue

        try:
            adjusted_base = config.adjust_path(base_dir.strip())
            logger.info(f"Processing base directory {i}/{len(base_dirs)}: {adjusted_base}")

            if not os.path.exists(adjusted_base):
                logger.warning(f"Base directory not found: {adjusted_base}")
                continue

            logger.info(f"Base directory exists: {adjusted_base}")

            # Try to list the directory to ensure it's accessible
            try:
                contents = os.listdir(adjusted_base)
                logger.info(f"Directory contains {len(contents)} items")
                if len(contents) > 0:
                    logger.info(f"First few items: {', '.join(contents[:5])}")
            except Exception as e:
                logger.error(f"Error listing directory {adjusted_base}: {str(e)}")
                continue

            logger.info(f"Traversing base directory: {adjusted_base}")

            # Walk the directory up to the specified depth - with enhanced error handling
            walk_count = 0
            log_interval = 100  # Log progress every 100 directories

            for root, dirs, files in _safe_walk(adjusted_base, logger):
                walk_count += 1

                # Calculate the current directory depth
                rel_path = os.path.relpath(root, adjusted_base)
                depth = len(rel_path.split(os.sep)) if rel_path != '.' else 0

                # Log progress periodically
                if walk_count % log_interval == 0:
                    logger.info(f"Processed {walk_count} directories, found {len(sections)} sections")

                # Normalize the path
                normalized_root = config.normalize_path(root)

                # Add the directory as a section
                sections.add(normalized_root)

                # Stop traversing if maximum depth is reached
                if depth >= max_depth - 1:
                    dirs.clear()  # Prevents further traversal

                # Avoid processing too many directories at once by limiting the number of entries
                if len(dirs) > 100:
                    logger.info(f"Limiting directory traversal in {root} from {len(dirs)} to 100 entries")
                    dirs[:] = dirs[:100]

                # Check for hidden directories and skip them
                dirs[:] = [d for d in dirs if not d.startswith('.')]

        except Exception as e:
            logger.error(f"Error processing base directory {base_dir}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    # Sort the sections
    sorted_sections = sorted(list(sections))
    logger.info(f"Found {len(sorted_sections)} sections across {len(base_dirs)} base directories")

    # Log first few sections for debugging
    if sorted_sections:
        logger.info("Sample of discovered sections:")
        for i, section in enumerate(sorted_sections[:10]):
            logger.info(f"  {i + 1}. {section}")

    return sorted_sections


def _safe_walk(directory, logger):
    """
    A safer version of os.walk that catches and logs errors instead of crashing.
    Includes timeout handling to avoid getting stuck on problematic directories.
    """
    try:
        # Use a custom walker that implements a timeout
        for root, dirs, files in _timeout_walk(directory, logger, timeout=30):
            yield root, dirs, files
    except Exception as e:
        logger.error(f"Exception in safe_walk for {directory}: {str(e)}")
        yield directory, [], []  # Return at least the base directory


def _timeout_walk(directory, logger, timeout=30):
    """
    A version of os.walk that implements a basic timeout for each directory.

    Args:
        directory: The directory to walk
        logger: Logger instance for error reporting
        timeout: Maximum time in seconds to spend in a single directory

    Yields:
        Same as os.walk: (root, dirs, files) tuples
    """
    try:
        # Process the top-level directory first
        try:
            entry_list = os.listdir(directory)
            dirs = []
            files = []

            # Split entries into directories and files
            for entry in entry_list:
                if entry.startswith('.'):
                    continue

                full_path = os.path.join(directory, entry)
                try:
                    if os.path.isdir(full_path):
                        dirs.append(entry)
                    else:
                        files.append(entry)
                except (OSError, PermissionError) as e:
                    logger.warning(f"Error checking path type for {full_path}: {e}")

            # Yield the current level
            yield directory, dirs, files

            # Process subdirectories with timeout
            for subdir in dirs:
                subdir_path = os.path.join(directory, subdir)

                # Apply a timeout for problematic directories
                start_time = time.time()
                subdir_processed = False

                try:
                    # Process the subdirectory
                    for root, d, f in _timeout_walk(subdir_path, logger, timeout):
                        yield root, d, f

                        # Check if we've exceeded the timeout
                        if time.time() - start_time > timeout:
                            logger.warning(f"Timeout reached when processing {subdir_path}, stopping traversal")
                            break

                    subdir_processed = True
                except Exception as e:
                    logger.warning(f"Error walking subdirectory {subdir_path}: {e}")

                # If we timed out or encountered an error, yield an empty result for this subdirectory
                if not subdir_processed:
                    logger.warning(f"Skipping problematic directory: {subdir_path}")
                    yield subdir_path, [], []

        except (OSError, PermissionError) as e:
            logger.warning(f"Error listing directory {directory}: {e}")
            yield directory, [], []

    except Exception as e:
        logger.error(f"Unexpected error in _timeout_walk for {directory}: {e}")
        yield directory, [], []


def get_section_name(section_path: str) -> str:
    """
    Generates a readable name for a section based on its path.

    Args:
        section_path: Full path to the section

    Returns:
        Readable name for the section
    """
    base_name = os.path.basename(section_path)
    parent_dir = os.path.basename(os.path.dirname(section_path))

    if parent_dir:
        return f"{parent_dir}/{base_name}"
    else:
        return base_name


def filter_sections(sections: List[str], include_patterns: Optional[List[str]] = None,
                    exclude_patterns: Optional[List[str]] = None) -> List[str]:
    """
    Filters sections based on inclusion and exclusion patterns.

    Args:
        sections: List of section paths
        include_patterns: List of patterns that must be included (optional)
        exclude_patterns: List of patterns that should be excluded (optional)

    Returns:
        Filtered list of section paths
    """
    if not include_patterns and not exclude_patterns:
        return sections

    filtered_sections = []

    for section in sections:
        # Check exclusion patterns
        if exclude_patterns:
            exclude = False
            for pattern in exclude_patterns:
                if pattern and pattern in section:
                    exclude = True
                    break

            if exclude:
                continue

        # Check inclusion patterns
        if include_patterns:
            include = False
            for pattern in include_patterns:
                if pattern and pattern in section:
                    include = True
                    break

            if not include:
                continue

        # If all filters have been passed, add the section
        filtered_sections.append(section)

    return filtered_sections