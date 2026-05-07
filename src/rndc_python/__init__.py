"""
rndc-python - A Python client library for ISC BIND's RNDC

This library provides a Python interface to ISC BIND's Remote Name Daemon Control (RNDC).
"""

from importlib.metadata import version

try:
    __version__ = version("rndc-python")
except Exception:  # noqa: BLE001 — zpapi-style fallback when package metadata is unavailable
    __version__ = "0.0.0+unknown"

__author__ = "David Groves"
__email__ = "dave@fibrecat.org"

# Import main classes and enums

from .enums import RNDCDataType, TSIGAlgorithm
from .exceptions import (
    RNDCAuthenticationError,
    RNDCConnectionError,
    RNDCError,
    RNDCZoneAlreadyExistsError,
    RNDCZoneNotFoundError,
)
from .rndc_client import RNDCClient
from .rndc_config import RNDCConfig, rndc_config

__all__ = [
    "__version__",
    "RNDCClient",
    "TSIGAlgorithm",
    "RNDCDataType",
    "RNDCError",
    "RNDCAuthenticationError",
    "RNDCConnectionError",
    "RNDCZoneNotFoundError",
    "RNDCZoneAlreadyExistsError",
    "RNDCConfig",
    "rndc_config",
]
