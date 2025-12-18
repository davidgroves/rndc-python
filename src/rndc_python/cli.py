"""
Command-line interface for rndc-python.

Usage:
    rndc-python-cli [options] <command>

Examples:
    rndc-python-cli status
    rndc-python-cli reload
    rndc-python-cli zonestatus example.com
    rndc-python-cli --host 127.0.0.1 --port 953 status
"""

from __future__ import annotations

import sys

import click

ALGORITHM_CHOICES = [
    "md5",
    "sha1",
    "sha224",
    "sha256",
    "sha384",
    "sha512",
    "hmac-md5",
    "hmac-sha1",
    "hmac-sha224",
    "hmac-sha256",
    "hmac-sha384",
    "hmac-sha512",
]


@click.command()
@click.option(
    "-s",
    "--host",
    envvar="ZPAPI_RNDC_HOST",
    help="RNDC server hostname or IP",
)
@click.option(
    "-p",
    "--port",
    type=int,
    envvar="ZPAPI_RNDC_PORT",
    help="RNDC server port",
)
@click.option(
    "-a",
    "--algorithm",
    type=click.Choice(ALGORITHM_CHOICES, case_sensitive=False),
    envvar="ZPAPI_RNDC_ALGORITHM",
    help="TSIG algorithm",
)
@click.option(
    "-k",
    "--secret",
    envvar="ZPAPI_RNDC_SECRET",
    help="Base64-encoded RNDC secret key",
)
@click.option(
    "-t",
    "--timeout",
    type=int,
    envvar="ZPAPI_RNDC_TIMEOUT",
    default=10,
    help="Connection timeout in seconds",
)
@click.argument("command", nargs=-1, required=True)
def main(
    host: str | None,
    port: int | None,
    algorithm: str | None,
    secret: str | None,
    timeout: int,
    command: tuple[str, ...],
) -> None:
    """Python client for ISC BIND's RNDC.

    COMMAND is the RNDC command to execute (e.g., status, reload, zonestatus example.com).
    """
    # Lazy imports to avoid triggering global config at import time
    from .rndc_client import RNDCClient
    from .rndc_config import _parse_algorithm

    # Validate required options
    if not host:
        raise click.ClickException("Missing --host or ZPAPI_RNDC_HOST environment variable")
    if not port:
        raise click.ClickException("Missing --port or ZPAPI_RNDC_PORT environment variable")
    if not algorithm:
        raise click.ClickException(
            "Missing --algorithm or ZPAPI_RNDC_ALGORITHM environment variable"
        )
    if not secret:
        raise click.ClickException("Missing --secret or ZPAPI_RNDC_SECRET environment variable")

    # Build client kwargs
    client_kwargs: dict = {
        "host": host,
        "port": port,
        "algorithm": _parse_algorithm(algorithm),
        "secret": secret,
        "timeout": timeout,
    }

    # Join command parts into a single RNDC command string
    rndc_command = " ".join(command)

    try:
        with RNDCClient(**client_kwargs) as client:
            result = client.call(rndc_command)

            # Print the response
            if "text" in result:
                click.echo(result["text"])
            elif "err" in result and result["err"]:
                raise click.ClickException(result["err"])
            elif result:
                # Print any other response data
                for key, value in result.items():
                    if key not in ("type", "result"):
                        click.echo(f"{key}: {value}")

            # Check result code if present
            if result.get("result") and result["result"] != "0":
                sys.exit(int(result["result"]))

    except click.ClickException:
        raise
    except ValueError as e:
        raise click.ClickException(f"Configuration error: {e}") from None
    except ConnectionError as e:
        raise click.ClickException(f"Connection error: {e}") from None
    except Exception as e:
        raise click.ClickException(str(e)) from None


if __name__ == "__main__":
    main()
