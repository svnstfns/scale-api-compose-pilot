"""
Pydantic models for the VideoInventory API.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel

class SectionStatus(BaseModel):
    """Model for section status response."""
    section_path: str
    status: str
    total_files: Optional[int] = None
    total_directories: Optional[int] = None
    updated_at: str


class InventoryItem(BaseModel):
    """Model for inventory item response."""
    file_id: str
    filepath: str
    filename: str
    mimetype: Optional[str] = None
    size: int
    size_hr: str
    status: str
    created_at: str


class ErrorLog(BaseModel):
    """Model for error log response."""
    file_path: str
    file_name: str
    issue: str
    timestamp: str


class Stats(BaseModel):
    """Model for statistics response."""
    total_files: int = 0
    mp4_files: int = 0
    indexed_files: int = 0
    errors: int = 0
    counted_sections: int = 0
    indexed_sections: int = 0


class SectionStats(BaseModel):
    """Model for section statistics response."""
    total: int = 0
    completed: int = 0
    in_progress: int = 0
    pending: int = 0
    error: int = 0


class ActivityItem(BaseModel):
    """Model for activity item response."""
    timestamp: str
    message: str