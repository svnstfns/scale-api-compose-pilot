"""
Dashboard routes for the VideoInventory web interface.
Provides statistics and activity data.
"""
from typing import List
from fastapi import HTTPException
from app.web.models import Stats, SectionStats, ActivityItem
from app.web import app
from app.db_utils import execute_query


@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """Return statistics about the system."""
    try:
        stats = Stats()

        # Get total files counted
        files_result = execute_query("SELECT SUM(total_files) as total FROM file_counts", fetch=True)
        if files_result and files_result[0]['total']:
            stats.total_files = files_result[0]['total']

        # Get MP4 file count
        mp4_result = execute_query(
            "SELECT COUNT(*) as count FROM inventory WHERE mimetype = 'video/mp4'",
            fetch=True
        )
        if mp4_result:
            stats.mp4_files = mp4_result[0]['count'] or 0

        # Get indexed files count
        indexed_result = execute_query(
            "SELECT COUNT(*) as count FROM inventory",
            fetch=True
        )
        if indexed_result:
            stats.indexed_files = indexed_result[0]['count'] or 0

        # Get error count
        error_result = execute_query(
            "SELECT COUNT(*) as count FROM error_log",
            fetch=True
        )
        if error_result:
            stats.errors = error_result[0]['count'] or 0

        # Get counted and indexed sections
        counted_result = execute_query(
            "SELECT COUNT(*) as count FROM section_status WHERE status IN ('counted', 'indexing', 'completed')",
            fetch=True
        )
        if counted_result:
            stats.counted_sections = counted_result[0]['count'] or 0

        indexed_result = execute_query(
            "SELECT COUNT(*) as count FROM section_status WHERE status IN ('completed')",
            fetch=True
        )
        if indexed_result:
            stats.indexed_sections = indexed_result[0]['count'] or 0

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/section_stats", response_model=SectionStats)
async def get_section_stats():
    """Return statistics about section processing."""
    try:
        stats = SectionStats()

        # Get total sections
        total_result = execute_query(
            "SELECT COUNT(*) as count FROM section_status",
            fetch=True
        )
        if total_result:
            stats.total = total_result[0]['count'] or 0

        # Get completed sections
        completed_result = execute_query(
            "SELECT COUNT(*) as count FROM section_status WHERE status = 'completed'",
            fetch=True
        )
        if completed_result:
            stats.completed = completed_result[0]['count'] or 0

        # Get in progress sections
        in_progress_result = execute_query(
            "SELECT COUNT(*) as count FROM section_status WHERE status IN ('counting', 'counted', 'indexing')",
            fetch=True
        )
        if in_progress_result:
            stats.in_progress = in_progress_result[0]['count'] or 0

        # Get pending sections - assume anything not counted or in progress is pending
        stats.pending = stats.total - stats.completed - stats.in_progress

        # Get error sections
        error_result = execute_query(
            "SELECT COUNT(*) as count FROM section_status WHERE status = 'error'",
            fetch=True
        )
        if error_result:
            stats.error = error_result[0]['count'] or 0

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/activity", response_model=List[ActivityItem])
async def get_recent_activity():
    """Return recent activity from logs and database events."""
    try:
        activity = []

        # Get recent section status changes
        section_updates = execute_query("""
            SELECT 
                section_path || ' status changed to: ' || status as message,
                updated_at as timestamp
            FROM section_status
            ORDER BY updated_at DESC
            LIMIT 10
        """, fetch=True)

        if section_updates:
            for update in section_updates:
                activity.append({
                    "timestamp": update["timestamp"],
                    "message": update["message"]
                })

        # Get recent errors
        error_updates = execute_query("""
            SELECT 
                'Error processing file: ' || file_name || ' - ' || substr(issue, 1, 100) as message,
                timestamp
            FROM error_log
            ORDER BY timestamp DESC
            LIMIT 5
        """, fetch=True)

        if error_updates:
            for update in error_updates:
                activity.append({
                    "timestamp": update["timestamp"],
                    "message": update["message"]
                })

        # Get recent inventory additions
        inventory_updates = execute_query("""
            SELECT 
                'Added file to inventory: ' || filename as message,
                created_at as timestamp
            FROM inventory
            ORDER BY created_at DESC
            LIMIT 5
        """, fetch=True)

        if inventory_updates:
            for update in inventory_updates:
                activity.append({
                    "timestamp": update["timestamp"],
                    "message": update["message"]
                })

        # Sort by timestamp and return
        return sorted(activity, key=lambda x: x["timestamp"], reverse=True)[:10]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")