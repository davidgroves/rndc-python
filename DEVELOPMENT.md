# Development

## Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/davidgroves/rndc-python.git
cd rndc-python
uv sync
```

## Building

Produce a wheel and source archive:

```bash
uv build
```

The built artifacts will be in the `dist/` directory.

## Testing

### Install test dependencies

```bash
uv sync --extra test
```

### Run all tests (requires Docker)

To run all tests including integration tests against a real BIND9 container:

```bash
uv run pytest
```

### Run unit tests (no Docker required)

To run only the unit tests (excludes integration tests that require Docker):

```bash
uv run pytest -m "not integration"
```

The integration tests use [testcontainers](https://testcontainers-python.readthedocs.io/) to spin up an ISC BIND9 Docker container automatically.

### Test configuration

The BIND9 test server configuration is in [tests/fixtures/named.conf](tests/fixtures/named.conf).

## Code Quality

### Install dev dependencies

```bash
uv sync --extra dev
```

### Pre-commit hooks

Install the pre-commit hooks to automatically check code before commits:

```bash
uv run pre-commit install
```

The hooks will run:
- **ruff** - linting with auto-fix
- **ruff-format** - code formatting
- **ty** - type checking

To run all hooks manually:

```bash
uv run pre-commit run --all-files
```
