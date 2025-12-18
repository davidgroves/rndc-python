"""
RNDC protocol implementation.

This module handles the low-level RNDC protocol message serialization and deserialization.
"""

import hashlib
import hmac
import struct

from .enums import RNDCDataType, TSIGAlgorithm
from .exceptions import RNDCConnectionError


def serialize_dict(data: dict, ignore_auth: bool = False) -> bytes:
    """Serialize dictionary to RNDC message format."""
    result = []

    for key, value in data.items():
        if ignore_auth and key == "_auth":
            continue

        result.append(chr(len(key)).encode())
        result.append(key.encode())

        if isinstance(value, str):
            result.append(struct.pack(">BI", RNDCDataType.RAW, len(value)))
            result.append(value.encode())
        elif isinstance(value, bytes):
            result.append(struct.pack(">BI", RNDCDataType.RAW, len(value)))
            result.append(value)
        elif isinstance(value, dict):
            serialized = serialize_dict(value)
            result.append(struct.pack(">BI", RNDCDataType.DICT, len(serialized)))
            result.append(serialized)
        else:
            raise ValueError(f"Cannot serialize type {type(value)}")

    return b"".join(result)


def parse_element(data: bytes) -> tuple[str, bytes | dict, bytes]:
    """Parse a single element from RNDC message."""
    if len(data) < 2:
        raise RNDCConnectionError("Incomplete message data")

    # Parse label
    label_len = data[0]
    if len(data) < 1 + label_len + 5:
        raise RNDCConnectionError("Incomplete message data")

    label = data[1 : 1 + label_len].decode("utf-8")
    pos = 1 + label_len

    # Parse type and length
    data_type = data[pos]
    pos += 1
    data_len = struct.unpack(">I", data[pos : pos + 4])[0]
    pos += 4

    if len(data) < pos + data_len:
        raise RNDCConnectionError("Incomplete message data")

    element_data = data[pos : pos + data_len]
    remaining = data[pos + data_len :]

    # Parse based on type
    if data_type == RNDCDataType.RAW:
        return label, element_data, remaining
    elif data_type == RNDCDataType.DICT:
        result = {}
        while element_data:
            sub_label, sub_value, element_data = parse_element(element_data)
            result[sub_label] = sub_value
        return label, result, remaining
    else:
        raise NotImplementedError(f"Unsupported data type: {data_type}")


def parse_message(data: bytes) -> dict:
    """Parse complete RNDC message."""
    result = {}
    while data:
        label, value, data = parse_element(data)
        result[label] = value
    return result


def create_hmac(secret: bytes, data: bytes, algorithm: TSIGAlgorithm) -> bytes:
    """Create HMAC for message authentication."""
    hash_algorithm = getattr(hashlib, algorithm.name.lower())
    return hmac.new(secret, data, hash_algorithm).digest()


def verify_hmac(secret: bytes, data: bytes, algorithm: TSIGAlgorithm, remote_hash: bytes) -> bool:
    """Verify HMAC for message authentication."""
    expected_hash = create_hmac(secret, data, algorithm)
    return hmac.compare_digest(expected_hash, remote_hash)
