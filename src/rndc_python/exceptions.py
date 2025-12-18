"""
RNDC exceptions.

This module contains custom exceptions used by the RNDC client.
"""


class RNDCError(Exception):
    """Base exception for RNDC-related errors."""

    pass


class RNDCAuthenticationError(RNDCError):
    """Raised when authentication fails."""

    pass


class RNDCConnectionError(RNDCError):
    """Raised when connection or communication fails."""

    pass


class RNDCZoneNotFoundError(RNDCError):
    """Raised when a zone is not found."""

    pass


class RNDCZoneAlreadyExistsError(RNDCError):
    """Raised when a zone already exists."""

    pass
