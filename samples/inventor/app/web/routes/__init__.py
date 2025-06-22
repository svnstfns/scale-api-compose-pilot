"""
Routes package initialization for VideoInventory.
This makes all route modules available to the FastAPI app.
"""

from app.web.routes import dashboard, sections, inventory, logs, health

# Create default __all__ for package exports
__all__ = ['dashboard', 'sections', 'inventory', 'logs', 'health']