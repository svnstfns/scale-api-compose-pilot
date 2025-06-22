"""
Web Service module for the VideoInventory application.
This module provides a REST API and web interface for monitoring the inventory process,
viewing statistics, and checking system status.

This file now serves as a compatibility layer to maintain backward compatibility
with the rest of the application while using the new modular structure.
"""

import os
import threading
from app.web.app import start_server, run_in_thread
from app.web.utils import initialize_templates
from app.web import app

# Initialize the templates
initialize_templates()

# For backward compatibility, expose the same functions as before
__all__ = ['start_server', 'run_in_thread', 'app']

if __name__ == "__main__":
    start_server()