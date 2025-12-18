import base64
import importlib
import struct
import time

from rndc_python import rndc_protocol
from rndc_python.enums import TSIGAlgorithm


class FakeSocket:
    """Simple fake socket that replays prebuilt responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.sent = []
        self.closed = False

    def send(self, data):
        self.sent.append(data)
        return len(data)

    def recv(self, n, flags=None):
        if not self.responses:
            return b""
        data = self.responses[0]
        chunk = data[:n]
        self.responses[0] = data[n:]
        if not self.responses[0]:
            self.responses.pop(0)
        return chunk

    def getpeername(self):
        return ("127.0.0.1", 953)

    def close(self):
        self.closed = True


def build_response(secret, algorithm, data, nonce=None, serial="1"):
    message = {
        "_auth": {},
        "_ctrl": {"_ser": serial, "_tim": str(int(time.time())), "_exp": "999999"},
        "_data": data,
    }
    if nonce is not None:
        message["_ctrl"]["_nonce"] = nonce

    serialized = rndc_protocol.serialize_dict(message, ignore_auth=True)
    digest = rndc_protocol.create_hmac(secret, serialized, algorithm)
    b64_hash = base64.b64encode(digest)

    if algorithm == TSIGAlgorithm.MD5:
        message["_auth"]["hmd5"] = struct.pack("22s", b64_hash)
    else:
        message["_auth"]["hsha"] = struct.pack("B88s", algorithm, b64_hash)

    final_msg = rndc_protocol.serialize_dict(message)
    return struct.pack(">II", len(final_msg) + 4, 1) + final_msg


def test_prepare_message_contains_auth(monkeypatch, env_vars, disable_env_file):
    import rndc_python.rndc_client as rndc_client

    monkeypatch.setattr(rndc_client.RNDCClient, "_connect", lambda self: None)
    client = rndc_client.RNDCClient(
        host="127.0.0.1",
        port=953,
        algorithm=TSIGAlgorithm.SHA256,
        secret=env_vars["ZPAPI_RNDC_SECRET"],
        timeout=5,
        max_retries=1,
        retry_delay=0.1,
    )
    client._nonce = "nonce"

    message = client._prepare_message(type="status")
    # Strip transport header
    payload = message[8:]
    parsed = rndc_protocol.parse_message(payload)

    assert parsed["_ctrl"]["_nonce"] == b"nonce"
    assert "_auth" in parsed
    assert parsed["_data"]["type"] == b"status"


def test_call_decodes_bytes(monkeypatch, env_vars, disable_env_file):
    import rndc_python.rndc_client as rndc_client

    importlib.reload(rndc_client)
    secret = base64.b64decode(env_vars["ZPAPI_RNDC_SECRET"])
    handshake = build_response(
        secret=secret, algorithm=TSIGAlgorithm.SHA256, data={"result": "ok"}, nonce="abc"
    )
    command_response = build_response(
        secret=secret,
        algorithm=TSIGAlgorithm.SHA256,
        data={"result": b"ok"},
        nonce="abc",
        serial="2",
    )

    fake_socket = FakeSocket([handshake, command_response])
    monkeypatch.setattr(
        rndc_client.socket, "create_connection", lambda *args, **kwargs: fake_socket
    )

    client = rndc_client.RNDCClient(
        host="127.0.0.1",
        port=953,
        algorithm=TSIGAlgorithm.SHA256,
        secret=env_vars["ZPAPI_RNDC_SECRET"],
        timeout=5,
        max_retries=1,
        retry_delay=0.1,
    )

    result = client.call("status")

    assert result["result"] == "ok"
    assert len(fake_socket.sent) == 2  # handshake + command

