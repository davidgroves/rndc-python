# rndc-python

Python client library for talking to ISC BIND's RNDC service.

## Requirements

- Python 3.10+

## Installation

```bash
pip install rndc-python
```

Or using uv:

```bash
uv add rndc-python
```

### Command-line Interface

The package includes a CLI tool `rndc-python-cli`:

```bash
# Using CLI options
rndc-python-cli -s 127.0.0.1 -p 953 -a sha256 -k <base64-secret> status

# Using environment variables
export ZPAPI_RNDC_HOST=127.0.0.1
export ZPAPI_RNDC_PORT=953
export ZPAPI_RNDC_ALGORITHM=sha256
export ZPAPI_RNDC_SECRET=<base64-secret>
rndc-python-cli status

# Mix of both (CLI options override env vars)
rndc-python-cli --port 954 reload
```

## Configuration

The client can read its settings from environment variables (or a `.env` file):

- `ZPAPI_RNDC_HOST`
- `ZPAPI_RNDC_PORT`
- `ZPAPI_RNDC_ALGORITHM` (e.g. `hmac-sha256`)
- `ZPAPI_RNDC_SECRET`
- `ZPAPI_RNDC_TIMEOUT`
- `ZPAPI_RNDC_MAX_RETRIES`
- `ZPAPI_RNDC_RETRY_DELAY`

You can also configure the client directly in Python:

```python
from rndc_python import RNDCClient, TSIGAlgorithm

client = RNDCClient(
    host="127.0.0.1",
    port=953,
    algorithm=TSIGAlgorithm.SHA256,
    secret="your-base64-secret-here",
    timeout=10,
    max_retries=3,
    retry_delay=2,
)
```

All parameters are optional if you have configured environment variables or a `.env` file.

## Usage

### Python API

```python
from rndc_python import RNDCClient

with RNDCClient() as rndc_client:
    print(rndc_client.call("status"))
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for development setup, building, and testing instructions.
