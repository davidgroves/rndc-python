from importlib import import_module, reload

import pytest

from rndc_python import config as cfg


def test_rndc_config_loads_env(env_vars, disable_env_file):
    rndc_config = import_module("rndc_python.rndc_config")
    reloaded = reload(rndc_config)
    conf = reloaded.RNDCConfig()

    assert conf.host == env_vars["ZPAPI_RNDC_HOST"]
    assert conf.port == int(env_vars["ZPAPI_RNDC_PORT"])
    assert conf.algorithm.name == "SHA256"
    assert conf.secret == env_vars["ZPAPI_RNDC_SECRET"]
    assert conf.timeout == int(env_vars["ZPAPI_RNDC_TIMEOUT"])
    assert conf.max_retries == int(env_vars["ZPAPI_RNDC_MAX_RETRIES"])
    assert conf.retry_delay == float(env_vars["ZPAPI_RNDC_RETRY_DELAY"])


def test_rndc_config_missing_env_raises(monkeypatch, disable_env_file):
    rndc_config_module = import_module("rndc_python.rndc_config")
    for key in [
        "ZPAPI_RNDC_HOST",
        "ZPAPI_RNDC_PORT",
        "ZPAPI_RNDC_ALGORITHM",
        "ZPAPI_RNDC_SECRET",
        "ZPAPI_RNDC_TIMEOUT",
    ]:
        monkeypatch.delenv(key, raising=False)

    # Creating RNDCConfig directly should raise ValueError
    with pytest.raises(ValueError):
        rndc_config_module.RNDCConfig()

    # The global rndc_config should be None when env vars are missing
    reloaded = reload(rndc_config_module)
    assert reloaded.rndc_config is None


@pytest.mark.parametrize(
    "port",
    ["0", "70000", "not-a-port"],
)
def test_parse_port_invalid(port):
    with pytest.raises(ValueError):
        cfg._parse_port(port)


@pytest.mark.parametrize(
    "timeout",
    ["0", "-1", "not-a-timeout"],
)
def test_parse_timeout_invalid(timeout):
    with pytest.raises(ValueError):
        cfg._parse_timeout(timeout)

