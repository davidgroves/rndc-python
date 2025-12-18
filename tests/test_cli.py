"""Tests for the CLI module."""

import pytest
from click.testing import CliRunner

from rndc_python.cli import main


@pytest.fixture
def runner():
    """Create a CLI test runner with isolated environment."""
    return CliRunner(
        env={
            "ZPAPI_RNDC_HOST": None,
            "ZPAPI_RNDC_PORT": None,
            "ZPAPI_RNDC_ALGORITHM": None,
            "ZPAPI_RNDC_SECRET": None,
            "ZPAPI_RNDC_TIMEOUT": None,
        }
    )


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_help_displays(self, runner):
        """Test that --help displays usage information."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "RNDC server hostname" in result.output
        assert "TSIG algorithm" in result.output
        assert "COMMAND" in result.output


class TestCLIMissingOptions:
    """Tests for CLI with missing required options."""

    def test_missing_command(self, runner):
        """Test that missing command produces an error."""
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "COMMAND" in result.output

    def test_missing_host(self, runner):
        """Test that missing host produces an error."""
        result = runner.invoke(
            main,
            [
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )
        assert result.exit_code != 0
        assert "Missing --host" in result.output

    def test_missing_port(self, runner):
        """Test that missing port produces an error."""
        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )
        assert result.exit_code != 0
        assert "Missing --port" in result.output

    def test_missing_algorithm(self, runner):
        """Test that missing algorithm produces an error."""
        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )
        assert result.exit_code != 0
        assert "Missing --algorithm" in result.output

    def test_missing_secret(self, runner):
        """Test that missing secret produces an error."""
        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "status",
            ],
        )
        assert result.exit_code != 0
        assert "Missing --secret" in result.output


class TestCLIEnvironmentVariables:
    """Tests for CLI with environment variables."""

    def test_env_vars_are_used(self, runner, mocker):
        """Test that environment variables are used when options not provided."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "server is running"}

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            ["status"],
            env={
                "ZPAPI_RNDC_HOST": "testhost",
                "ZPAPI_RNDC_PORT": "953",
                "ZPAPI_RNDC_ALGORITHM": "sha256",
                "ZPAPI_RNDC_SECRET": "dGVzdHNlY3JldA==",
            },
        )

        assert result.exit_code == 0
        assert "server is running" in result.output

    def test_cli_options_override_env_vars(self, runner, mocker):
        """Test that CLI options override environment variables."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "ok"}

        mock_client_class = mocker.patch(
            "rndc_python.rndc_client.RNDCClient", return_value=mock_client
        )

        result = runner.invoke(
            main,
            ["--host", "clihost", "--port", "9953", "status"],
            env={
                "ZPAPI_RNDC_HOST": "envhost",
                "ZPAPI_RNDC_PORT": "953",
                "ZPAPI_RNDC_ALGORITHM": "sha256",
                "ZPAPI_RNDC_SECRET": "dGVzdHNlY3JldA==",
            },
        )

        assert result.exit_code == 0
        # Verify CLI values were used instead of env vars
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["host"] == "clihost"
        assert call_kwargs["port"] == 9953


class TestCLICommandExecution:
    """Tests for CLI command execution."""

    def test_simple_command(self, runner, mocker):
        """Test executing a simple command."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "server is up and running"}

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )

        assert result.exit_code == 0
        assert "server is up and running" in result.output
        mock_client.call.assert_called_once_with("status")

    def test_command_with_arguments(self, runner, mocker):
        """Test executing a command with multiple arguments."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "zone info"}

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "zonestatus",
                "example.com",
            ],
        )

        assert result.exit_code == 0
        # Command arguments should be joined
        mock_client.call.assert_called_once_with("zonestatus example.com")

    def test_response_with_error_field(self, runner, mocker):
        """Test handling response with err field."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"err": "zone not found"}

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "zonestatus",
                "nonexistent.com",
            ],
        )

        assert result.exit_code != 0
        assert "zone not found" in result.output

    def test_response_with_nonzero_result(self, runner, mocker):
        """Test handling response with non-zero result code."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "command failed", "result": "1"}

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "badcommand",
            ],
        )

        assert result.exit_code == 1

    def test_response_with_other_fields(self, runner, mocker):
        """Test handling response with arbitrary fields."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {
            "type": "response",
            "result": "0",
            "custom_field": "custom_value",
            "another": "data",
        }

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "customcmd",
            ],
        )

        assert result.exit_code == 0
        assert "custom_field: custom_value" in result.output
        assert "another: data" in result.output
        # type and result should not be printed
        assert "type:" not in result.output


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_connection_error(self, runner, mocker):
        """Test handling connection errors."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(side_effect=ConnectionError("Connection refused"))

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )

        assert result.exit_code != 0
        assert "Connection error" in result.output

    def test_value_error(self, runner, mocker):
        """Test handling ValueError (configuration errors)."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(
            side_effect=ValueError("Invalid secret key format")
        )

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "invalid!!!",
                "status",
            ],
        )

        assert result.exit_code != 0
        assert "Configuration error" in result.output

    def test_generic_exception(self, runner, mocker):
        """Test handling generic exceptions."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.side_effect = RuntimeError("Unexpected error")

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )

        assert result.exit_code != 0
        assert "Unexpected error" in result.output


class TestCLIAlgorithmChoices:
    """Tests for CLI algorithm validation."""

    @pytest.mark.parametrize(
        "algorithm",
        ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"],
    )
    def test_valid_algorithms(self, runner, mocker, algorithm):
        """Test that valid algorithm names are accepted."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "ok"}

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                algorithm,
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )

        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "algorithm",
        ["hmac-md5", "hmac-sha1", "hmac-sha224", "hmac-sha256", "hmac-sha384", "hmac-sha512"],
    )
    def test_valid_hmac_algorithms(self, runner, mocker, algorithm):
        """Test that valid HMAC algorithm names are accepted."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "ok"}

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                algorithm,
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )

        assert result.exit_code == 0

    def test_invalid_algorithm_rejected(self, runner):
        """Test that invalid algorithm names are rejected."""
        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "invalid-algo",
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid-algo" in result.output

    def test_algorithm_case_insensitive(self, runner, mocker):
        """Test that algorithm names are case-insensitive."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "ok"}

        mocker.patch("rndc_python.rndc_client.RNDCClient", return_value=mock_client)

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "SHA256",  # uppercase
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )

        assert result.exit_code == 0


class TestCLITimeout:
    """Tests for CLI timeout option."""

    def test_default_timeout(self, runner, mocker):
        """Test that default timeout is 10 seconds."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "ok"}

        mock_client_class = mocker.patch(
            "rndc_python.rndc_client.RNDCClient", return_value=mock_client
        )

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "status",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["timeout"] == 10

    def test_custom_timeout(self, runner, mocker):
        """Test that custom timeout is passed through."""
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.MagicMock(return_value=mock_client)
        mock_client.__exit__ = mocker.MagicMock(return_value=False)
        mock_client.call.return_value = {"text": "ok"}

        mock_client_class = mocker.patch(
            "rndc_python.rndc_client.RNDCClient", return_value=mock_client
        )

        result = runner.invoke(
            main,
            [
                "--host",
                "localhost",
                "--port",
                "953",
                "--algorithm",
                "sha256",
                "--secret",
                "dGVzdHNlY3JldA==",
                "--timeout",
                "30",
                "status",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["timeout"] == 30
