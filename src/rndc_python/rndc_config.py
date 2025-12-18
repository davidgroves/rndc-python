"""
RNDC configuration management.

This module handles loading RNDC configuration from environment variables.
Assumes .env file contains all required defaults if they aren't set in the environment.
"""

from typing import Any

from .config import (
    _get_required_env_var,
    _load_env_file,
    _parse_float_env_var,
    _parse_int_env_var,
    _parse_port,
    _parse_timeout,
)
from .enums import TSIGAlgorithm


def _parse_algorithm(algorithm_str: str) -> TSIGAlgorithm:
    """Parse algorithm string to RNDCAlgorithm enum."""
    algorithm_map = {
        "md5": TSIGAlgorithm.MD5,
        "sha1": TSIGAlgorithm.SHA1,
        "sha224": TSIGAlgorithm.SHA224,
        "sha256": TSIGAlgorithm.SHA256,
        "sha384": TSIGAlgorithm.SHA384,
        "sha512": TSIGAlgorithm.SHA512,
    }
    algorithm_lower_and_stripped = algorithm_str.lower().removeprefix("hmac-")
    if algorithm_lower_and_stripped not in algorithm_map:
        raise ValueError(f"Unsupported algorithm: {algorithm_str}")
    return algorithm_map[algorithm_lower_and_stripped]


class RNDCConfig:
    """RNDC configuration loaded from environment variables."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        algorithm: TSIGAlgorithm | None = None,
        secret: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
    ) -> None:
        _load_env_file()
        self.host = host or _get_required_env_var("ZPAPI_RNDC_HOST")
        self.port = port or _parse_port(_get_required_env_var("ZPAPI_RNDC_PORT"))
        self.algorithm = algorithm or _parse_algorithm(
            _get_required_env_var("ZPAPI_RNDC_ALGORITHM")
        )
        self.secret = secret or _get_required_env_var("ZPAPI_RNDC_SECRET")
        self.timeout = timeout or _parse_timeout(_get_required_env_var("ZPAPI_RNDC_TIMEOUT"))
        self.max_retries = max_retries or _parse_int_env_var("ZPAPI_RNDC_MAX_RETRIES", 3)
        self.retry_delay = retry_delay or _parse_float_env_var("ZPAPI_RNDC_RETRY_DELAY", 1.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "algorithm": self.algorithm,
            "secret": self.secret,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }

    def __repr__(self) -> str:
        return (
            f"RNDCConfig(host='{self.host}', port={self.port}, "
            f"algorithm={self.algorithm.name}, timeout={self.timeout}, "
            f"max_retries={self.max_retries}, retry_delay={self.retry_delay})"
        )


# Global RNDC config instance (lazy - only created when env vars are available)
def _create_default_config() -> RNDCConfig | None:
    """Create a default config if environment variables are set."""
    try:
        return RNDCConfig()
    except ValueError:
        # Environment variables not set - return None
        # Users should create RNDCConfig explicitly with parameters
        return None


rndc_config: RNDCConfig | None = _create_default_config()
