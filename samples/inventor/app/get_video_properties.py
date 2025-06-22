# app/get_video_properties.py
"""
Video Properties module for the VideoInventory application.
This module extracts technical properties from video files using ffmpeg,
including codec, resolution, quality, and duration and stores them in the database.
"""

import os
import logging
import ffmpeg
from datetime import timedelta
import platform
from app.db_utils import execute_query, get_connection
from app.logger import setup_logger

# Configure logging
logger = setup_logger("video_properties")


def insert_error_log(file_path, file_name, issue):
    """
    Inserts an error record into the error_log table.

    Args:
        file_path: Path to the file that caused the error
        file_name: Name of the file
        issue: Description of the error
    """
    try:
        execute_query("""
            INSERT INTO error_log (file_path, file_name, issue, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                issue=?,
                timestamp=CURRENT_TIMESTAMP
        """, (file_path, file_name, issue, issue))

        logger.info(f"Inserted error log for {file_path} with issue: {issue}")
    except Exception as e:
        logger.error(f"Failed to insert error log: {e}")


def convert_duration(seconds):
    """
    Converts duration in seconds to hours:minutes:seconds format.

    Args:
        seconds: Duration in seconds

    Returns:
        Duration as a formatted string
    """
    return str(timedelta(seconds=int(seconds)))


def get_video_info(filepath):
    """
    Gets video information using ffmpeg.

    Args:
        filepath: Path to the video file

    Returns:
        Tuple of (codec_name, resolution, quality, duration) or None if error
    """
    logger.info(f'Getting video info for {filepath}')
    try:
        # Probe the video file using ffmpeg-python
        probe = ffmpeg.probe(filepath, select_streams='v:0', show_entries='stream=codec_name,width,height,duration',
                             of='json')
        video_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    except ffmpeg.Error as e:
        logger.error(f'Error during probing: