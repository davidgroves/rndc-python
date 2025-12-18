"""
RNDC client implementation.

This module contains the main RNDC client class for communicating with BIND DNS servers.
"""

import base64
import ipaddress
import logging
import random
import socket
import struct
import time
import typing

import dns
import dns.rdataclass

from . import rndc_protocol
from .enums import TSIGAlgorithm
from .exceptions import (
    RNDCAuthenticationError,
    RNDCConnectionError,
    RNDCZoneAlreadyExistsError,
    RNDCZoneNotFoundError,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RNDCClient:
    """RNDC client for communicating with BIND DNS servers."""

    def __init__(
        self,
        host: str | ipaddress.IPv4Address | ipaddress.IPv6Address | None = None,
        port: int | None = None,
        algorithm: TSIGAlgorithm | None = None,
        secret: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
    ) -> None:
        """Initialize RNDC client."""

        # Import here to avoid circular imports
        from .rndc_config import rndc_config

        # Use provided values or fall back to environment configuration (if available)
        # rndc_config may be None if env vars are not set
        if host is not None:
            self.host = host
        elif rndc_config is not None:
            self.host = rndc_config.host
        else:
            raise ValueError("host is required (provide it or set ZPAPI_RNDC_HOST)")

        if port is not None:
            self.port = port
        elif rndc_config is not None:
            self.port = rndc_config.port
        else:
            raise ValueError("port is required (provide it or set ZPAPI_RNDC_PORT)")

        if algorithm is not None:
            self.algorithm = algorithm
        elif rndc_config is not None:
            self.algorithm = rndc_config.algorithm
        else:
            raise ValueError("algorithm is required (provide it or set ZPAPI_RNDC_ALGORITHM)")

        if secret is not None:
            self.secret = base64.b64decode(secret)
        elif rndc_config is not None:
            self.secret = base64.b64decode(rndc_config.secret)
        else:
            raise ValueError("secret is required (provide it or set ZPAPI_RNDC_SECRET)")

        if timeout is not None:
            self.timeout = timeout
        elif rndc_config is not None:
            self.timeout = rndc_config.timeout
        else:
            self.timeout = 10  # Default timeout

        if max_retries is not None:
            self.max_retries = max_retries
        elif rndc_config is not None:
            self.max_retries = rndc_config.max_retries
        else:
            self.max_retries = 3  # Default max retries

        if retry_delay is not None:
            self.retry_delay = retry_delay
        elif rndc_config is not None:
            self.retry_delay = rndc_config.retry_delay
        else:
            self.retry_delay = 1.0  # Default retry delay

        # Internal state
        self._serial = random.randint(0, 1 << 24)
        self._nonce: str | None = None
        self._socket: socket.socket | None = None

        # Establish connection
        self._connect()

    def _connect(self) -> None:
        """Establish connection to RNDC server and perform initial handshake."""
        logger.info(f"Connecting to RNDC server at {self.host}:{self.port}")
        try:
            self._socket = socket.create_connection(
                (str(self.host), self.port), timeout=self.timeout
            )
            self._nonce = None

            # Perform null command to get nonce
            response = self._command(type="null")
            self._nonce = response["_ctrl"]["_nonce"]

        except OSError as e:
            raise RNDCConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}") from e

    def _ensure_connected(self) -> None:
        """Ensure we have a valid connection, reconnecting if necessary."""
        if self._socket is None:
            logger.info("No socket connection, reconnecting...")
            self._connect()
            return

        # Test if the connection is still alive by trying to get socket info
        try:
            # This will raise an exception if the socket is closed
            self._socket.getpeername()
        except OSError:
            logger.info("Socket connection lost, reconnecting...")
            self._socket.close()
            self._socket = None
            self._nonce = None
            self._connect()

    def _prepare_message(self, **kwargs: typing.Any) -> bytes:
        """Prepare RNDC message with authentication."""
        self._serial += 1
        now = int(time.time())

        # Build message structure
        message = {
            "_auth": {},
            "_ctrl": {
                "_ser": str(self._serial),
                "_tim": str(now),
                "_exp": str(now + 60),
            },
            "_data": kwargs,
        }

        if self._nonce is not None:
            message["_ctrl"]["_nonce"] = self._nonce

        # Serialize without auth for hashing
        serialized = rndc_protocol.serialize_dict(message, ignore_auth=True)

        # Create HMAC
        hash_digest = rndc_protocol.create_hmac(self.secret, serialized, self.algorithm)
        b64_hash = base64.b64encode(hash_digest)

        # Add authentication
        if self.algorithm == TSIGAlgorithm.MD5:
            message["_auth"]["hmd5"] = struct.pack("22s", b64_hash)
        else:
            message["_auth"]["hsha"] = struct.pack("B88s", self.algorithm, b64_hash)

        # Final serialization
        final_msg = rndc_protocol.serialize_dict(message)
        return struct.pack(">II", len(final_msg) + 4, 1) + final_msg

    def _verify_message(self, message: dict) -> bool:
        """Verify message authentication."""
        if self._nonce is not None and message["_ctrl"]["_nonce"] != self._nonce:
            return False

        # Extract hash
        auth_key = "hmd5" if self.algorithm == TSIGAlgorithm.MD5 else "hsha"
        hash_data = message["_auth"][auth_key]

        # For SHA algorithms, the first byte is the algorithm ID, followed by base64 hash
        if self.algorithm != TSIGAlgorithm.MD5:
            # Skip the algorithm ID byte and extract the base64 hash
            b64_hash = hash_data[1:].rstrip(b"\x00").decode("ascii")
        else:
            # For MD5, it's just the base64 hash
            b64_hash = hash_data.rstrip(b"\x00").decode("ascii")

        # Pad base64 if needed
        b64_hash += "=" * (4 - (len(b64_hash) % 4))

        try:
            remote_hash = base64.b64decode(b64_hash)
        except Exception:
            return False

        # Verify hash
        my_msg = rndc_protocol.serialize_dict(message, ignore_auth=True)
        return rndc_protocol.verify_hmac(self.secret, my_msg, self.algorithm, remote_hash)

    def _command(self, **kwargs: typing.Any) -> dict:
        """Send command to RNDC server and receive response."""
        # Ensure we have a valid connection before proceeding
        self._ensure_connected()

        if self._socket is None:
            raise RNDCConnectionError("Not connected to RNDC server")

        # Prepare and send message
        message = self._prepare_message(**kwargs)
        sent = self._socket.send(message)
        if sent != len(message):
            raise RNDCConnectionError("Failed to send complete message")

        # Receive header
        header = self._socket.recv(8)
        if len(header) != 8:
            raise RNDCAuthenticationError("Failed to read response header")

        # Parse header
        msg_len, version = struct.unpack(">II", header)
        if version != 1:
            raise NotImplementedError(f"Unsupported message version: {version}")

        # Receive message body
        msg_len -= 4  # Remove header size
        data = self._socket.recv(msg_len, socket.MSG_WAITALL)
        if len(data) != msg_len:
            raise RNDCConnectionError("Failed to read complete response")

        # Parse and verify message
        parsed_msg = rndc_protocol.parse_message(data)
        if not self._verify_message(parsed_msg):
            raise RNDCAuthenticationError("Message authentication failed")

        return parsed_msg

    def call(self, command: str) -> dict[str, str]:
        """
        Execute RNDC command.

        Args:
            command: RNDC command string (e.g., 'status', 'reload zone example.com')

        Returns:
            Command response data with values decoded from ASCII bytes to strings
        """
        logger.info(f"Running command {command}")
        response = self._command(type=command)
        logger.info(f"Response: {response}")

        # Decode response as ASCII if appropriate.
        return {
            k: v.decode("ascii") if isinstance(v, bytes) else v
            for k, v in response["_data"].items()
        }

    def close(self) -> None:
        """Close the RNDC connection."""
        if self._socket:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> "RNDCClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: typing.Any, exc_val: typing.Any, exc_tb: typing.Any) -> None:
        """Context manager exit."""
        self.close()

    def add_zone(
        self,
        name: str,
        dnsclass: dns.rdataclass.RdataClass = dns.rdataclass.IN,
        view: str | None = None,
        template: str | None = "primary",
    ) -> None:
        """Add a zone to the RNDC server."""
        cmd = f"addzone {name} {dnsclass.name} {view or ''} {{template {template};}};"
        result = self.call(cmd)

        # Safely check if result exists and has the expected structure
        if result.get("result") == "16" and result.get("err") == "already exists":
            raise RNDCZoneAlreadyExistsError(f"Zone {name} already exists")

    def del_zone(
        self,
        name: str,
        clean: bool = False,
        dnsclass: dns.rdataclass.RdataClass = dns.rdataclass.IN,
        view: str | None = None,
    ) -> None:
        """Delete a zone from the RNDC server."""
        suffix = f"{name} {dnsclass.name} {view or ''}"

        if clean:
            result = self.call(f"delzone -clean {suffix}")
        else:
            result = self.call(f"delzone {suffix}")

        if result.get("result") == "20" and result.get("err") == "not found":
            raise RNDCZoneNotFoundError(f"Zone {name} not found")

    def set_trace_level(self, level: int) -> None:
        if level < 0 or level > 99:
            raise ValueError("Trace level must be an integer between 0 and 99")

        """Set the trace level for the RNDC server."""
        self.call(f"trace {level}")

    def send_notify(
        self,
        zone: str,
        view: str | None = None,
        dnsclass: dns.rdataclass.RdataClass = dns.rdataclass.IN,
    ) -> None:
        """Forces server to send a notify for a zone."""
        result = self.call(f"notify {zone} {view or ''} {dnsclass.name}")
        if result.get("result") == "20" and result.get("err") == "not found":
            raise RNDCZoneNotFoundError(f"Zone {zone} not found")
