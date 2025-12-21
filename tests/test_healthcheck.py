"""Tests for the healthcheck script."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from scripts.healthcheck import (
    get_missing_required_keys,
    main,
    parse_args,
    probe_url,
)


class TestParseArgs:
    """Tests for argument parsing."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        args = parse_args([])
        assert args.url == "http://localhost:8501/"
        assert args.timeout == 5.0
        assert args.allow_missing_secrets is False

    def test_custom_url(self):
        """Test custom URL argument."""
        args = parse_args(["--url", "http://example.com:8080/"])
        assert args.url == "http://example.com:8080/"

    def test_custom_timeout(self):
        """Test custom timeout argument."""
        args = parse_args(["--timeout", "10.5"])
        assert args.timeout == 10.5

    def test_allow_missing_secrets_flag(self):
        """Test allow-missing-secrets flag."""
        args = parse_args(["--allow-missing-secrets"])
        assert args.allow_missing_secrets is True


class TestGetMissingRequiredKeys:
    """Tests for secret validation."""

    def test_all_secrets_present(self):
        """Test when all required secrets are present."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            missing = get_missing_required_keys(allow_missing_secrets=False)
            assert missing == []

    def test_missing_single_secret(self):
        """Test when one required secret is missing."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
            clear=True,
        ):
            missing = get_missing_required_keys(allow_missing_secrets=False)
            assert missing == ["GOOGLE_SEARCH_API_KEY"]

    def test_missing_multiple_secrets(self):
        """Test when multiple required secrets are missing."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
            },
            clear=True,
        ):
            missing = get_missing_required_keys(allow_missing_secrets=False)
            assert set(missing) == {
                "REDDIT_CLIENT_ID",
                "REDDIT_CLIENT_SECRET",
                "GOOGLE_SEARCH_API_KEY",
                "GOOGLE_SEARCH_ENGINE_ID",
            }

    def test_allow_missing_secrets_returns_empty_list(self):
        """Test that allow_missing_secrets=True bypasses validation."""
        with mock.patch.dict(os.environ, {}, clear=True):
            missing = get_missing_required_keys(allow_missing_secrets=True)
            assert missing == []


class TestProbeUrl:
    """Tests for URL probing."""

    def test_successful_probe_returns_status(self):
        """Test that probe_url returns status code on success."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_response):
            status = probe_url("http://example.com/", timeout=5.0)
            assert status == 200

    def test_probe_url_creates_correct_request(self):
        """Test that probe_url creates a request with the correct URL."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            with mock.patch("urllib.request.Request") as mock_request:
                probe_url("http://example.com/", timeout=5.0)
                mock_request.assert_called_once_with("http://example.com/")


class TestMain:
    """Tests for main function integration."""

    def test_main_success_with_all_secrets(self, capsys):
        """Test successful health check with all secrets present."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            mock_response = mock.MagicMock()
            mock_response.status = 200
            mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
            mock_response.__exit__ = mock.MagicMock(return_value=False)

            with mock.patch("urllib.request.urlopen", return_value=mock_response):
                exit_code = main([])
                assert exit_code == 0

    def test_main_fails_with_missing_secrets(self, capsys):
        """Test that main fails when required secrets are missing."""
        with mock.patch.dict(os.environ, {}, clear=True):
            exit_code = main([])
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "Missing required secrets" in captured.err

    def test_main_succeeds_with_allow_missing_secrets(self, capsys):
        """Test that main succeeds with --allow-missing-secrets flag."""
        with mock.patch.dict(os.environ, {}, clear=True):
            mock_response = mock.MagicMock()
            mock_response.status = 200
            mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
            mock_response.__exit__ = mock.MagicMock(return_value=False)

            with mock.patch("urllib.request.urlopen", return_value=mock_response):
                exit_code = main(["--allow-missing-secrets"])
                assert exit_code == 0

    def test_main_fails_on_http_error_status(self, capsys):
        """Test that main fails when HTTP status is >= 400."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            mock_response = mock.MagicMock()
            mock_response.status = 500
            mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
            mock_response.__exit__ = mock.MagicMock(return_value=False)

            with mock.patch("urllib.request.urlopen", return_value=mock_response):
                exit_code = main([])
                assert exit_code == 1
                captured = capsys.readouterr()
                assert "Health probe returned HTTP 500" in captured.err

    def test_main_fails_on_http_1xx_status(self, capsys):
        """Test that main fails when HTTP status is < 200."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            mock_response = mock.MagicMock()
            mock_response.status = 100
            mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
            mock_response.__exit__ = mock.MagicMock(return_value=False)

            with mock.patch("urllib.request.urlopen", return_value=mock_response):
                exit_code = main([])
                assert exit_code == 1
                captured = capsys.readouterr()
                assert "Health probe returned HTTP 100" in captured.err

    def test_main_accepts_2xx_status(self):
        """Test that main accepts 2xx status codes."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            for status in [200, 201, 204]:
                mock_response = mock.MagicMock()
                mock_response.status = status
                mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
                mock_response.__exit__ = mock.MagicMock(return_value=False)

                with mock.patch("urllib.request.urlopen", return_value=mock_response):
                    exit_code = main([])
                    assert exit_code == 0

    def test_main_accepts_3xx_status(self):
        """Test that main accepts 3xx status codes."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            for status in [301, 302, 304]:
                mock_response = mock.MagicMock()
                mock_response.status = status
                mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
                mock_response.__exit__ = mock.MagicMock(return_value=False)

                with mock.patch("urllib.request.urlopen", return_value=mock_response):
                    exit_code = main([])
                    assert exit_code == 0

    def test_main_fails_on_url_error(self, capsys):
        """Test that main handles URLError with specific message."""
        import urllib.error

        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            with mock.patch(
                "urllib.request.urlopen",
                side_effect=urllib.error.URLError("Connection refused"),
            ):
                exit_code = main([])
                assert exit_code == 1
                captured = capsys.readouterr()
                assert "Health probe connection failed" in captured.err

    def test_main_fails_on_timeout(self, capsys):
        """Test that main handles timeout with specific message."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            with mock.patch(
                "urllib.request.urlopen",
                side_effect=TimeoutError("Timeout occurred"),
            ):
                exit_code = main(["--timeout", "2.0"])
                assert exit_code == 1
                captured = capsys.readouterr()
                assert "Health probe timed out after 2.0s" in captured.err

    def test_main_handles_unexpected_errors(self, capsys):
        """Test that main handles unexpected errors gracefully."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            with mock.patch(
                "urllib.request.urlopen",
                side_effect=ValueError("Unexpected error"),
            ):
                exit_code = main([])
                assert exit_code == 1
                captured = capsys.readouterr()
                assert "Health probe failed with unexpected error" in captured.err

    def test_main_respects_custom_timeout(self):
        """Test that main uses custom timeout value."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "REDDIT_CLIENT_ID": "test-id",
                "REDDIT_CLIENT_SECRET": "test-secret",
                "GOOGLE_SEARCH_API_KEY": "test-google-key",
                "GOOGLE_SEARCH_ENGINE_ID": "test-engine-id",
            },
        ):
            mock_response = mock.MagicMock()
            mock_response.status = 200
            mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
            mock_response.__exit__ = mock.MagicMock(return_value=False)

            with mock.patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
                main(["--timeout", "15.0"])
                # Check that urlopen was called with the timeout
                call_args = mock_urlopen.call_args
                assert call_args[1]["timeout"] == 15.0
