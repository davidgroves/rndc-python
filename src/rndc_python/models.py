"""
Data models for RNDC responses.

This module contains typed dataclasses for parsing RNDC command responses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar


@dataclass
class Status:
    """Parsed RNDC status response.

    Represents the status of a BIND DNS server as returned by the 'status' command.
    """

    # Version and system info
    version: str
    """BIND version string (e.g., 'BIND 9.20.15-2-Debian (Stable Release)')"""

    running_on: str
    """System information where BIND is running"""

    boot_time: datetime
    """When the server was started"""

    last_configured: datetime
    """When the server was last configured/reloaded"""

    configuration_file: str
    """Path to the named.conf configuration file"""

    # Resource info
    cpus_found: int
    """Number of CPUs detected"""

    worker_threads: int
    """Number of worker threads"""

    # Zone info
    number_of_zones: int
    """Total number of zones"""

    automatic_zones: int
    """Number of automatic zones (built-in zones like localhost)"""

    # Debug and logging
    debug_level: int
    """Current debug level (0 = off)"""

    query_logging: bool
    """Whether query logging is enabled"""

    response_logging: bool
    """Whether response logging is enabled"""

    memory_profiling_active: bool
    """Whether memory profiling is active"""

    # Transfer status
    xfers_running: int
    """Number of zone transfers currently running"""

    xfers_deferred: int
    """Number of zone transfers deferred"""

    xfers_first_refresh: int
    """Number of zones waiting for first refresh"""

    soa_queries_in_progress: int
    """Number of SOA queries in progress"""

    # Client connections
    recursive_clients_current: int
    """Current number of recursive clients"""

    recursive_clients_soft_limit: int
    """Soft limit for recursive clients"""

    recursive_clients_hard_limit: int
    """Hard limit for recursive clients"""

    recursive_high_water: int
    """High water mark for recursive clients"""

    tcp_clients_current: int
    """Current number of TCP clients"""

    tcp_clients_limit: int
    """Limit for TCP clients"""

    tcp_high_water: int
    """High water mark for TCP clients"""

    # Server state
    server_is_up: bool
    """Whether the server is up and running"""

    # Raw text for any unparsed fields
    raw_text: str
    """The raw status text from RNDC"""

    # Date format used by BIND
    _DATE_FORMAT: ClassVar[str] = "%a, %d %b %Y %H:%M:%S %Z"

    @classmethod
    def from_text(cls, text: str) -> Status:
        """Parse status text into a Status object.

        Args:
            text: Raw status text from RNDC status command

        Returns:
            Parsed Status object
        """

        def get_value(pattern: str, default: str = "") -> str:
            """Extract a value using regex pattern."""
            match = re.search(pattern, text, re.MULTILINE)
            return match.group(1).strip() if match else default

        def get_int(pattern: str, default: int = 0) -> int:
            """Extract an integer value using regex pattern."""
            value = get_value(pattern)
            try:
                return int(value) if value else default
            except ValueError:
                return default

        def parse_datetime(pattern: str) -> datetime:
            """Parse a datetime value using regex pattern."""
            value = get_value(pattern)
            if not value:
                return datetime.min
            try:
                return datetime.strptime(value, cls._DATE_FORMAT)
            except ValueError:
                return datetime.min

        def parse_bool_on_off(pattern: str) -> bool:
            """Parse an ON/OFF boolean value."""
            value = get_value(pattern).upper()
            return value == "ON"

        def parse_bool_active(pattern: str) -> bool:
            """Parse an ACTIVE/INACTIVE boolean value."""
            value = get_value(pattern).upper()
            return value == "ACTIVE"

        # Parse zones with automatic count
        zones_match = re.search(r"number of zones:\s*(\d+)\s*(?:\((\d+)\s*automatic\))?", text)
        number_of_zones = int(zones_match.group(1)) if zones_match else 0
        automatic_zones = int(zones_match.group(2)) if zones_match and zones_match.group(2) else 0

        # Parse recursive clients: current/soft/hard
        recursive_match = re.search(r"recursive clients:\s*(\d+)/(\d+)/(\d+)", text)
        if recursive_match:
            recursive_current = int(recursive_match.group(1))
            recursive_soft = int(recursive_match.group(2))
            recursive_hard = int(recursive_match.group(3))
        else:
            recursive_current = recursive_soft = recursive_hard = 0

        # Parse TCP clients: current/limit
        tcp_match = re.search(r"tcp clients:\s*(\d+)/(\d+)", text, re.IGNORECASE)
        if tcp_match:
            tcp_current = int(tcp_match.group(1))
            tcp_limit = int(tcp_match.group(2))
        else:
            tcp_current = tcp_limit = 0

        return cls(
            version=get_value(r"^version:\s*(.+)$"),
            running_on=get_value(r"^running on [^:]+:\s*(.+)$"),
            boot_time=parse_datetime(r"^boot time:\s*(.+)$"),
            last_configured=parse_datetime(r"^last configured:\s*(.+)$"),
            configuration_file=get_value(r"^configuration file:\s*(.+)$"),
            cpus_found=get_int(r"^CPUs found:\s*(\d+)"),
            worker_threads=get_int(r"^worker threads:\s*(\d+)"),
            number_of_zones=number_of_zones,
            automatic_zones=automatic_zones,
            debug_level=get_int(r"^debug level:\s*(\d+)"),
            query_logging=parse_bool_on_off(r"^query logging is\s*(\w+)"),
            response_logging=parse_bool_on_off(r"^response logging is\s*(\w+)"),
            memory_profiling_active=parse_bool_active(r"^memory profiling is\s*(\w+)"),
            xfers_running=get_int(r"^xfers running:\s*(\d+)"),
            xfers_deferred=get_int(r"^xfers deferred:\s*(\d+)"),
            xfers_first_refresh=get_int(r"^xfers first refresh:\s*(\d+)"),
            soa_queries_in_progress=get_int(r"^soa queries in progress:\s*(\d+)"),
            recursive_clients_current=recursive_current,
            recursive_clients_soft_limit=recursive_soft,
            recursive_clients_hard_limit=recursive_hard,
            recursive_high_water=get_int(r"^recursive high-water:\s*(\d+)"),
            tcp_clients_current=tcp_current,
            tcp_clients_limit=tcp_limit,
            tcp_high_water=get_int(r"^TCP high-water:\s*(\d+)", 0),
            server_is_up="server is up and running" in text.lower(),
            raw_text=text,
        )
