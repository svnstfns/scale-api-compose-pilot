"""
Scale API Compose Pilot

Pilot Docker Compose workloads to TrueNAS Scale via WebSocket API.
AI-friendly automation tool with comprehensive error handling and validation.
"""

from .manager import TrueNASDockerManager
from .exceptions import TrueNASConnectionError, TrueNASAuthenticationError, TrueNASAPIError
from .ai_helper import AIHelper, create_ai_summary

__version__ = "0.1.0"
__author__ = "sst"
__email__ = "svnstfns@gmail.com"

__all__ = [
    "TrueNASDockerManager",
    "AIHelper",
    "TrueNASConnectionError", 
    "TrueNASAuthenticationError",
    "TrueNASAPIError",
    "create_ai_summary"
]