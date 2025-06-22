"""
Sections routes for the VideoInventory web interface.
Provides information about discovered sections and their processing status.
"""
from typing import List
from fastapi import HTTPException
from app.web.models import SectionStatus
from app.web import app
from app.db_utils import execute_query


@app.get("/api/sections", response_model=List[SectionStatus])
async def get_sections():
    """Return all section statuses."""
    try:
        # Join section_status and file_counts tables
        sections = execute_query("""
            SELECT ss.section_path, ss.status, ss.updated_at, 
                   fc.total_files, fc.total_directories
            FROM section_status ss
            LEFT JOIN file_counts fc ON ss.section_path = fc.share_name
            ORDER BY ss.updated_at DESC
        """, fetch=True)

        return sections or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")