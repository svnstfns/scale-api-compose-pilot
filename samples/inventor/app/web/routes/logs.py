"""
Logs routes for the VideoInventory web interface.
Provides access to application logs.
"""
from fastapi import HTTPException
from app.web import app
from app.web.utils import read_all_logs


@app.get("/api/logs")
async def get_logs():
    """Return all logs."""
    try:
        return read_all_logs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")