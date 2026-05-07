"""Tests for the models module."""

import pytest

from rndc_python.models import Status

# Sample status output from BIND 9.20
SAMPLE_STATUS_TEXT = """version: BIND 9.20.15-2-Debian (Stable Release) <id:>
running on localhost: Linux x86_64 6.17.11+deb14-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.17.11-1 (2025-12-07)
boot time: Thu, 18 Dec 2025 20:11:58 GMT
last configured: Thu, 18 Dec 2025 20:11:58 GMT
configuration file: /etc/bind/named.conf
CPUs found: 16
worker threads: 16
number of zones: 101 (100 automatic)
debug level: 0
xfers running: 0
xfers deferred: 0
xfers first refresh: 0
soa queries in progress: 0
query logging is OFF
response logging is OFF
memory profiling is INACTIVE
recursive clients: 0/900/1000
recursive high-water: 0
tcp clients: 0/150
TCP high-water: 0
server is up and running
"""


class TestStatusParsing:
    """Tests for Status.from_text() parsing."""

    def test_parse_version(self):
        """Test parsing version string."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.version == "BIND 9.20.15-2-Debian (Stable Release) <id:>"

    def test_parse_running_on(self):
        """Test parsing running on system info."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert "Linux x86_64" in status.running_on

    def test_parse_boot_time(self):
        """Test parsing boot time."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.boot_time.year == 2025
        assert status.boot_time.month == 12
        assert status.boot_time.day == 18
        assert status.boot_time.hour == 20
        assert status.boot_time.minute == 11
        assert status.boot_time.second == 58

    def test_parse_last_configured(self):
        """Test parsing last configured time."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.last_configured.year == 2025
        assert status.last_configured.month == 12
        assert status.last_configured.day == 18

    def test_parse_configuration_file(self):
        """Test parsing configuration file path."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.configuration_file == "/etc/bind/named.conf"

    def test_parse_cpus_found(self):
        """Test parsing CPUs found."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.cpus_found == 16

    def test_parse_worker_threads(self):
        """Test parsing worker threads."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.worker_threads == 16

    def test_parse_number_of_zones(self):
        """Test parsing number of zones."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.number_of_zones == 101
        assert status.automatic_zones == 100

    def test_parse_debug_level(self):
        """Test parsing debug level."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.debug_level == 0

    def test_parse_query_logging(self):
        """Test parsing query logging status."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.query_logging is False

    def test_parse_query_logging_on(self):
        """Test parsing query logging when ON."""
        text = SAMPLE_STATUS_TEXT.replace("query logging is OFF", "query logging is ON")
        status = Status.from_text(text)
        assert status.query_logging is True

    def test_parse_response_logging(self):
        """Test parsing response logging status."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.response_logging is False

    def test_parse_memory_profiling(self):
        """Test parsing memory profiling status."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.memory_profiling_active is False

    def test_parse_memory_profiling_active(self):
        """Test parsing memory profiling when ACTIVE."""
        text = SAMPLE_STATUS_TEXT.replace(
            "memory profiling is INACTIVE", "memory profiling is ACTIVE"
        )
        status = Status.from_text(text)
        assert status.memory_profiling_active is True

    def test_parse_xfers_running(self):
        """Test parsing xfers running."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.xfers_running == 0

    def test_parse_xfers_deferred(self):
        """Test parsing xfers deferred."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.xfers_deferred == 0

    def test_parse_xfers_first_refresh(self):
        """Test parsing xfers first refresh."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.xfers_first_refresh == 0

    def test_parse_soa_queries_in_progress(self):
        """Test parsing SOA queries in progress."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.soa_queries_in_progress == 0

    def test_parse_recursive_clients(self):
        """Test parsing recursive clients."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.recursive_clients_current == 0
        assert status.recursive_clients_soft_limit == 900
        assert status.recursive_clients_hard_limit == 1000

    def test_parse_recursive_high_water(self):
        """Test parsing recursive high water mark."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.recursive_high_water == 0

    def test_parse_tcp_clients(self):
        """Test parsing TCP clients."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.tcp_clients_current == 0
        assert status.tcp_clients_limit == 150

    def test_parse_tcp_high_water(self):
        """Test parsing TCP high water mark."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.tcp_high_water == 0

    def test_parse_server_is_up(self):
        """Test parsing server is up status."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.server_is_up is True

    def test_parse_server_not_running(self):
        """Test parsing when server is not running."""
        text = SAMPLE_STATUS_TEXT.replace("server is up and running", "server is shutting down")
        status = Status.from_text(text)
        assert status.server_is_up is False

    def test_raw_text_preserved(self):
        """Test that raw text is preserved."""
        status = Status.from_text(SAMPLE_STATUS_TEXT)
        assert status.raw_text == SAMPLE_STATUS_TEXT


class TestStatusDefaults:
    """Tests for Status default values when parsing incomplete data."""

    def test_missing_fields_have_defaults(self):
        """Test that missing fields get default values."""
        status = Status.from_text("")
        assert status.version == ""
        assert status.cpus_found == 0
        assert status.number_of_zones == 0
        assert status.query_logging is False
        assert status.server_is_up is False

    def test_partial_status(self):
        """Test parsing partial status output."""
        partial_text = """version: BIND 9.18.0
CPUs found: 4
server is up and running
"""
        status = Status.from_text(partial_text)
        assert status.version == "BIND 9.18.0"
        assert status.cpus_found == 4
        assert status.server_is_up is True
        assert status.worker_threads == 0  # Not in partial text


class TestStatusWithNonStandardValues:
    """Tests for Status with non-standard values."""

    @pytest.mark.parametrize(
        "zones_text,expected_total,expected_auto",
        [
            ("number of zones: 5", 5, 0),  # No automatic count
            ("number of zones: 100 (50 automatic)", 100, 50),
            ("number of zones: 0", 0, 0),
        ],
    )
    def test_various_zone_counts(self, zones_text, expected_total, expected_auto):
        """Test parsing various zone count formats."""
        text = f"version: test\n{zones_text}\n"
        status = Status.from_text(text)
        assert status.number_of_zones == expected_total
        assert status.automatic_zones == expected_auto

    @pytest.mark.parametrize(
        "clients_text,current,soft,hard",
        [
            ("recursive clients: 10/100/200", 10, 100, 200),
            ("recursive clients: 0/500/1000", 0, 500, 1000),
        ],
    )
    def test_various_recursive_client_values(self, clients_text, current, soft, hard):
        """Test parsing various recursive client values."""
        text = f"version: test\n{clients_text}\n"
        status = Status.from_text(text)
        assert status.recursive_clients_current == current
        assert status.recursive_clients_soft_limit == soft
        assert status.recursive_clients_hard_limit == hard
