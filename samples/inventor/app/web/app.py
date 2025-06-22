"""
Main web application module for VideoInventory.
"""
import threading
import uvicorn
from fastapi.responses import HTMLResponse
import os
from app.web import app
from app.config import Config

# Path to frontend files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "templates")

@app.get("/", response_class=HTMLResponse)
async def get_root():
    """Return the Vue.js application."""
    with open(os.path.join(STATIC_DIR, "index.html"), "r") as f:
        return f.read()

def start_server(host="0.0.0.0", port=88):
    """Start the FastAPI server."""
    # Set up uvicorn logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "use_colors": False,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO"},
        },
    }

    uvicorn.run(app, host=host, port=port, log_config=log_config)

def run_in_thread(host="0.0.0.0", port=88):
    """Run the FastAPI server in a separate thread."""
    server_thread = threading.Thread(target=start_server, args=(host, port))
    server_thread.daemon = True  # Thread will exit when main program exits
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    start_server()