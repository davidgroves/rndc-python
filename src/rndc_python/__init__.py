"""
rndc-python - A Python client library for ISC BIND's RNDC

This library provides a Python interface to ISC BIND's Remote Name Daemon Control (RNDC).
"""

__version__ = "0.1.0"
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
