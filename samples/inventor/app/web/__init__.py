"""
Web package initialization for VideoInventory.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Create the FastAPI app
app = FastAPI(title="VideoInventory API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes after app is created to avoid circular imports
from app.web.routes import dashboard, sections, inventory, logs, health

# Path to static directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount the static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Create default __all__ for package exports
__all__ = ['app']