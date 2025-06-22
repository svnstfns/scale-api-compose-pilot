"""
Inventory routes for the VideoInventory web interface.
Provides access to the inventory of video files.
"""
from typing import List
from fastapi import HTTPException
from app.web.models import InventoryItem, ErrorLog
from app.web import app
from app.db_utils import execute_query


@app.get("/api/inventory", response_model=List[InventoryItem])
async def get_inventory():
    """Return inventory items (with pagination in a real app)."""
    try:
        # Just return the most recent 100 items for efficiency
        inventory = execute_query("""
            SELECT * FROM inventory 
            ORDER BY created_at DESC 
            LIMIT 100
        """, fetch=True)

        return inventory or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/errors", response_model=List[ErrorLog])
async def get_errors():
    """Return error logs."""
    try:
        errors = execute_query("""
            SELECT * FROM error_log 
            ORDER BY timestamp DESC 
            LIMIT 100
        """, fetch=True)

        return errors or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")