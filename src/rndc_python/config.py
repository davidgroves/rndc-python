"""
Configuration utilities.

This module contains shared configuration functions and utilities used by both
RNDC and DDNS configuration modules.
"""

import os

from dotenv import load_dotenv


def _load_env_file() -> None:
    """Load environment variables from .env file if it exists."""
    if os.path.exists(".env"):
        load_dotenv(".env")


def _get_required_env_var(key: str) -> str:
    """Get required environment variable."""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def _parse_port(port_str: str) -> int:
    """Parse port string to integer."""
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got {port}")
        return port
    except ValueError as e:
        if isinstance(e, ValueError) and "Port must be between" in str(e):
            raise
        raise ValueError(f"Invalid port number: {port_str}") from e


def _parse_timeout(timeout_str: str) -> int:
    """Parse timeout string to integer."""
    try:
        timeout = int(timeout_str)
        if timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {timeout}")
        return timeout
    except ValueError as e:
        if isinstance(e, ValueError) and "Timeout must be positive" in str(e):
            raise
        raise ValueError(f"Invalid timeout value: {timeout_str}") from e


def _parse_int_env_var(key: str, default: int) -> int:
    """Parse integer environment variable with default value."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid integer value for {key}: {value}") from None


def _parse_float_env_var(key: str, default: float) -> float:
    """Parse float environment variable with default value."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid float value for {key}: {value}") from None
