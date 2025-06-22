"""
Health check route for the VideoInventory web interface.
Provides basic application health status information.
"""
from fastapi import HTTPException
from app.web import app
from app.db_utils import execute_query


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        execute_query("SELECT 1", fetch=True)

        # Return basic health information
        return {
            "status": "ok",
            "components": {
                "database": "online",
                "api": "online"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "components": {
                "database": "offline" if "database" in str(e).lower() else "unknown",
                "api": "online"
            }
        }