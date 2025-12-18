"""
RNDC enums and constants.

This module contains the enumeration classes and constants used by the RNDC protocol.
"""

import enum


class TSIGAlgorithm(enum.IntEnum):
    """TSIG authentication algorithms."""

    MD5 = 157
    SHA1 = 161
    SHA224 = 162
    SHA256 = 163
    SHA384 = 164
    SHA512 = 165


class RNDCDataType(enum.IntEnum):
    """RNDC data types for message serialization."""

    RAW = 1
    DICT = 2
    LIST = 3
