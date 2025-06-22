"""
Custom exceptions for TrueNAS Docker Manager.
"""


class TrueNASError(Exception):
    """Base exception class for TrueNAS operations."""
    pass


class TrueNASConnectionError(TrueNASError):
    """Raised when connection to TrueNAS fails."""
    pass


class TrueNASAuthenticationError(TrueNASError):
    """Raised when authentication with TrueNAS fails."""
    pass


class TrueNASAPIError(TrueNASError):
    """Raised when TrueNAS API calls fail."""
    pass


class DockerComposeError(TrueNASError):
    """Raised when Docker Compose conversion fails."""
    pass