import base64
import importlib
import os

import pytest

DEFAULT_ENV = {
    "ZPAPI_RNDC_HOST": "127.0.0.1",
    "ZPAPI_RNDC_PORT": "953",
    "ZPAPI_RNDC_ALGORITHM": "hmac-sha256",
    "ZPAPI_RNDC_SECRET": base64.b64encode(b"test-secret").decode(),
    "ZPAPI_RNDC_TIMEOUT": "5",
    "ZPAPI_RNDC_MAX_RETRIES": "2",
    "ZPAPI_RNDC_RETRY_DELAY": "0.1",
}

# Ensure base env is present before tests import the package
for key, value in DEFAULT_ENV.items():
    os.environ.setdefault(key, value)


@pytest.fixture
def env_vars(monkeypatch):
    """Provide baseline RNDC environment variables for tests."""
    for key, value in DEFAULT_ENV.items():
        monkeypatch.setenv(key, value)
    return DEFAULT_ENV.copy()


@pytest.fixture
def reload_rndc_config(env_vars):
    """Reload rndc_config with fresh env values."""
    import rndc_python.rndc_config as rndc_config

    return importlib.reload(rndc_config)


@pytest.fixture
def reload_rndc_client(env_vars):
    """Reload rndc_client with fresh env values."""
    import rndc_python.rndc_client as rndc_client

    return importlib.reload(rndc_client)


@pytest.fixture
def disable_env_file(monkeypatch):
    """Prevent loading a local .env during tests."""
    monkeypatch.setattr("rndc_python.config.os.path.exists", lambda path: False)
