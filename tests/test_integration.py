"""
Integration tests using a real BIND9 server via testcontainers.

These tests require Docker to be available. Run with:
    uv run --extra test pytest -m integration

To exclude integration tests:
    uv run --extra test pytest -m "not integration"
"""

from pathlib import Path

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from rndc_python import RNDCClient, TSIGAlgorithm

# Test RNDC key (base64 encoded "secret-key-for-testing-only")
TEST_RNDC_SECRET = "c2VjcmV0LWtleS1mb3ItdGVzdGluZy1vbmx5"

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class Bind9Container(DockerContainer):
    """BIND9 container configured for RNDC testing."""

    def __init__(self) -> None:
        super().__init__(image="internetsystemsconsortium/bind9:9.20")
        self.with_exposed_ports(953, 53)
        # Use -g flag to log to stderr (visible via docker logs)
        self.with_command("-g -c /etc/bind/named.conf")
        # Mount configuration files
        self.with_volume_mapping(
            str(FIXTURES_DIR / "named.conf"),
            "/etc/bind/named.conf",
            mode="ro",
        )
        self.with_volume_mapping(
            str(FIXTURES_DIR / "db.test.example"),
            "/etc/bind/db.test.example",
            mode="ro",
        )

    def get_rndc_port(self) -> int:
        return int(self.get_exposed_port(953))

    def get_dns_port(self) -> int:
        return int(self.get_exposed_port(53))


@pytest.fixture(scope="module")
def bind9_container():
    """Start a BIND9 container for integration tests."""
    container = Bind9Container()
    # Wait for BIND to log "running" indicating it's fully started using structured wait strategy
    container.waiting_for(LogMessageWaitStrategy("running"))
    container.start()

    yield container

    container.stop()


@pytest.fixture
def rndc_client(bind9_container):
    """Create an RNDCClient connected to the test container."""
    host = bind9_container.get_container_host_ip()
    port = bind9_container.get_rndc_port()

    client = RNDCClient(
        host=host,
        port=port,
        algorithm=TSIGAlgorithm.SHA256,
        secret=TEST_RNDC_SECRET,
        timeout=10,
        max_retries=3,
        retry_delay=0.5,
    )
    yield client
    client.close()


@pytest.mark.integration
class TestRNDCIntegration:
    """Integration tests for RNDC client against a real BIND9 server."""

    def test_status_command(self, rndc_client):
        """Test the status command returns server info."""
        result = rndc_client.call("status")

        assert "text" in result
        status_text = result["text"]
        assert "version" in status_text.lower() or "running" in status_text.lower()

    def test_reload_command(self, rndc_client):
        """Test the reload command succeeds."""
        result = rndc_client.call("reload")

        # Reload should succeed without error
        assert "err" not in result or result.get("err") == ""

    def test_flush_command(self, rndc_client):
        """Test the flush (cache clear) command."""
        result = rndc_client.call("flush")

        # Flush should succeed without error
        assert "err" not in result or result.get("err") == ""

    def test_zonestatus_command(self, rndc_client):
        """Test getting zone status for the test zone."""
        result = rndc_client.call("zonestatus test.example")

        assert "text" in result
        # Should contain zone info
        assert "test.example" in result["text"] or "name:" in result["text"].lower()

    def test_reconfig_command(self, rndc_client):
        """Test the reconfig command."""
        result = rndc_client.call("reconfig")

        # Reconfig should succeed
        assert "err" not in result or result.get("err") == ""

    def test_recursing_command(self, rndc_client):
        """Test dumping recursing queries."""
        result = rndc_client.call("recursing")

        # Should succeed (may or may not have output)
        assert "err" not in result or result.get("err") == ""

    def test_querylog_toggle(self, rndc_client):
        """Test toggling query logging."""
        # Enable query logging
        result = rndc_client.call("querylog on")
        assert "err" not in result or result.get("err") == ""

        # Disable query logging
        result = rndc_client.call("querylog off")
        assert "err" not in result or result.get("err") == ""

    def test_trace_level(self, rndc_client):
        """Test setting trace level."""
        rndc_client.set_trace_level(1)

        # Reset trace level
        rndc_client.set_trace_level(0)

    def test_context_manager(self, bind9_container):
        """Test using RNDCClient as a context manager."""
        host = bind9_container.get_container_host_ip()
        port = bind9_container.get_rndc_port()

        with RNDCClient(
            host=host,
            port=port,
            algorithm=TSIGAlgorithm.SHA256,
            secret=TEST_RNDC_SECRET,
            timeout=10,
        ) as client:
            result = client.call("status")
            assert "text" in result

    def test_multiple_commands_same_connection(self, rndc_client):
        """Test sending multiple commands on the same connection."""
        # First command
        result1 = rndc_client.call("status")
        assert "text" in result1

        # Second command
        result2 = rndc_client.call("reload")
        assert "err" not in result2 or result2.get("err") == ""

        # Third command
        result3 = rndc_client.call("status")
        assert "text" in result3


@pytest.mark.integration
class TestRNDCAuthenticationIntegration:
    """Integration tests for RNDC authentication."""

    def test_wrong_secret_fails(self, bind9_container):
        """Test that wrong secret causes authentication failure."""
        from rndc_python.exceptions import RNDCAuthenticationError

        host = bind9_container.get_container_host_ip()
        port = bind9_container.get_rndc_port()

        # Use wrong secret (different base64 string)
        with pytest.raises((RNDCAuthenticationError, Exception)):
            client = RNDCClient(
                host=host,
                port=port,
                algorithm=TSIGAlgorithm.SHA256,
                secret="d3Jvbmctc2VjcmV0LWtleS1mb3ItdGVzdGluZw==",
                timeout=5,
            )
            client.call("status")
            client.close()

    def test_wrong_algorithm_fails(self, bind9_container):
        """Test that wrong algorithm causes authentication failure."""
        from rndc_python.exceptions import RNDCAuthenticationError

        host = bind9_container.get_container_host_ip()
        port = bind9_container.get_rndc_port()

        # Server expects SHA256, try with SHA512
        with pytest.raises((RNDCAuthenticationError, Exception)):
            client = RNDCClient(
                host=host,
                port=port,
                algorithm=TSIGAlgorithm.SHA512,
                secret=TEST_RNDC_SECRET,
                timeout=5,
            )
            client.call("status")
            client.close()
