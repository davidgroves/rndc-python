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

### Versioning (git tags)

Package and sdist/wheel **version metadata** is derived from **git** via [hatch-vcs](https://github.com/ofek/hatch-vcs): builds use the latest reachable annotated/lightweight tag and commit distance (PEP 440), e.g. `v0.2.0` or a development suffix when not exactly on a tag.

- **Release tags:** Use a consistent form such as `v0.2.0` (leading `v` is conventional for hatch-vcs/setuptools-scm-style tooling).
- **Runtime:** `rndc_python.__version__` comes from `importlib.metadata.version("rndc-python")` (installed metadata), with a fallback if the distribution is missing (e.g. an unpacked source tree without install).
- **CI:** Jobs that build wheels or publish to PyPI must check out **full git history and tags** so the version can be computed—for example GitHub Actions `fetch-depth: 0` and fetching tags if needed. Shallow clones often produce wrong or unusable versions.

## Releasing

Pushing a tag matching `v*` runs [`.github/workflows/publish.yml`](.github/workflows/publish.yml): unit tests, `uv build`, then upload to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC). No `PYPI_API_TOKEN` is stored in the repo.

### One-time setup

1. Create a GitHub Environment named **`pypi`** on this repository (Settings → Environments), or allow the first tagged workflow run to create it when referenced.
2. On [PyPI → rndc-python → Publishing](https://pypi.org/manage/project/rndc-python/settings/publishing/), add a Trusted Publisher:
   - Owner: `davidgroves`
   - Repository: `rndc-python`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

### Publish a release

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Use a version that has not already been published on PyPI. The wheel/sdist version is taken from the tag by hatch-vcs.

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

### Regenerate code coverage.

```bash
uv run pytest --cov=src --cov-report=html
```
