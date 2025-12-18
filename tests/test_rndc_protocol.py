import base64

import pytest

from rndc_python import rndc_protocol
from rndc_python.enums import TSIGAlgorithm
from rndc_python.exceptions import RNDCConnectionError


def test_serialize_and_parse_roundtrip():
    message = {
        "_ctrl": {"_ser": "1", "_tim": "2"},
        "_data": {"msg": "hello", "nested": {"k": b"v"}},
        "_auth": {"token": b"abc"},
    }

    serialized = rndc_protocol.serialize_dict(message)
    parsed = rndc_protocol.parse_message(serialized)

    assert parsed["_ctrl"]["_ser"] == b"1"
    assert parsed["_data"]["msg"] == b"hello"
    assert parsed["_data"]["nested"]["k"] == b"v"
    assert parsed["_auth"]["token"] == b"abc"


def test_parse_incomplete_data_raises():
    with pytest.raises(RNDCConnectionError):
        rndc_protocol.parse_message(b"\x05short")


def test_hmac_create_and_verify():
    secret = b"secret-key"
    data = b"payload"

    digest = rndc_protocol.create_hmac(secret, data, TSIGAlgorithm.SHA256)
    assert rndc_protocol.verify_hmac(secret, data, TSIGAlgorithm.SHA256, digest)

    tampered = base64.b64decode(base64.b64encode(digest)[:-2] + b"AA")
    assert not rndc_protocol.verify_hmac(secret, data, TSIGAlgorithm.SHA256, tampered)

