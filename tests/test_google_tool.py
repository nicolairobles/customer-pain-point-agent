"""Unit tests for Google search tool functionality."""

from __future__ import annotations

import json
import os
import pytest
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, Any

from config.settings import APISettings, Settings, ToolSettings
from src.tools.google_search_tool import GoogleSearchTool


@pytest.fixture
def success_response() -> Dict[str, Any]:
    """Load successful Google search response fixture."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "google", "success_response.json")
    with open(fixture_path, "r") as f:
        return json.load(f)


@pytest.fixture
def zero_results_response() -> Dict[str, Any]:
    """Load zero results response fixture."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "google", "zero_results.json")
    with open(fixture_path, "r") as f:
        return json.load(f)


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        api=APISettings(
            google_search_api_key="dummy_api_key",
            google_search_engine_id="dummy_engine_id",
        ),
        tools=ToolSettings(reddit_enabled=False, google_search_enabled=True),
    )


def test_google_search_tool_success_response(success_response, test_settings: Settings) -> None:
    """Test successful Google search with normalized results."""
    from unittest.mock import patch, MagicMock

    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()

    mock_execute.return_value = success_response
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse

    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(test_settings)
        results = tool._run("test query")

        assert len(results) == 2
        assert results[0]["title"] == "Test Result 1"
        assert results[0]["text"] == "This is a test snippet"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["display_url"] == "example.com"
        assert results[0]["created_at"] == "2023-01-01"
        assert results[0]["ranking_position"] == 1
        assert results[0]["platform"] == "google_search"

        assert results[1]["ranking_position"] == 2
        assert results[1]["created_at"] == ""  # No date available


def test_google_search_tool_zero_results(zero_results_response, test_settings: Settings) -> None:
    """Test handling of zero search results."""
    from unittest.mock import patch, MagicMock

    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()

    mock_execute.return_value = zero_results_response
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse

    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(test_settings)
        results = tool._run("test query")

        assert results == []


def test_google_search_tool_quota_error_retry(test_settings: Settings) -> None:
    """Test quota error handling with retry logic."""
    from unittest.mock import patch, MagicMock
    from googleapiclient.errors import HttpError

    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()

    # Create a mock HttpError for quota exceeded
    quota_error = HttpError(Mock(status=403), b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}')
    quota_error.error_details = [{"reason": "quotaExceeded"}]

    # Mock successful response after retry
    mock_response = {
        "items": [{
            "title": "Success Result",
            "snippet": "Success snippet",
            "link": "https://example.com",
            "displayLink": "example.com"
        }]
    }

    # First call raises quota error, second returns success response
    mock_execute.side_effect = [quota_error, mock_response]
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse

    with patch('src.tools.google_search_tool.time.sleep', return_value=None), patch(
        'src.tools.google_search_tool.build', return_value=mock_client
    ):
        tool = GoogleSearchTool.from_settings(test_settings)
        results = tool._run("test query")

        assert len(results) == 1
        assert results[0]["title"] == "Success Result"
        # Verify execute was called twice (initial + retry)
        assert mock_execute.call_count == 2


def test_google_search_tool_malformed_response(test_settings: Settings) -> None:
    """Test handling of malformed API responses."""
    from unittest.mock import patch, MagicMock

    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()

    # Malformed response missing 'items' key
    mock_execute.return_value = {"error": "Something went wrong"}
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse

    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(test_settings)
        results = tool._run("test query")

        # Should return empty list for malformed responses
        assert results == []


def test_google_search_tool_logging_sanitization(test_settings: Settings) -> None:
    """Test that logging omits API keys while including correlation identifiers."""
    import logging
    from unittest.mock import patch, MagicMock

    # Capture log messages
    log_messages = []

    class MockLogger:
        def debug(self, message, *args, **kwargs):
            log_messages.append(message)

        def info(self, message, *args, **kwargs):
            log_messages.append(message)

        def warning(self, message, *args, **kwargs):
            log_messages.append(message)

        def error(self, message, *args, **kwargs):
            log_messages.append(message)

    # Mock the logger
    with patch('src.tools.google_search_tool._LOG', MockLogger()):
        mock_client = MagicMock()
        mock_cse = MagicMock()
        mock_list = MagicMock()
        mock_execute = MagicMock()

        mock_execute.return_value = {"items": []}
        mock_list.return_value.execute = mock_execute
        mock_cse.return_value.list = mock_list
        mock_client.cse = mock_cse

        with patch('src.tools.google_search_tool.build', return_value=mock_client):
            tool = GoogleSearchTool.from_settings(test_settings)
            results = tool._run("test query")

            # Check that log messages were captured and don't contain sensitive info
            assert len(log_messages) > 0
            for message in log_messages:
                assert "api_key" not in message.lower()
                assert "key=" not in message.lower()
                # Should contain generic logging info
                assert "Google Search" in message or "returning" in message


def test_google_search_tool_parameters(test_settings: Settings) -> None:
    """Test that search parameters are correctly passed to Google API."""
    from unittest.mock import patch, MagicMock

    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()

    mock_execute.return_value = {"items": []}
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse

    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(test_settings)
        results = tool._run("test query", num=5)

        # Verify API was called with correct parameters
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args[1]

        assert call_kwargs["q"] == "test query"
        assert call_kwargs["num"] == 5
        assert call_kwargs["cx"] == "dummy_engine_id"


def test_google_search_tool_failure_injection(test_settings: Settings) -> None:
    """Failure injection test - temporarily modify normalization to ensure tests fail when schema changes."""
    from unittest.mock import patch, MagicMock

    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()

    mock_response = {
        "items": [{
            "title": "Test",
            "snippet": "Test snippet",
            "link": "https://example.com",
            "displayLink": "example.com"
        }]
    }

    mock_execute.return_value = mock_response
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse

    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(test_settings)
        
        # Patch the _normalize_result method to return None (simulating a schema change)
        with patch.object(tool, '_normalize_result', return_value=None):
            results = tool._run("test query")

            # With broken normalization returning None, results should be filtered out
            assert len(results) == 0


def test_google_search_tool_accepts_customsearch_result_kind(test_settings: Settings) -> None:
    """Regression: real API items use kind=customsearch#result (should not be filtered out)."""
    from unittest.mock import MagicMock, patch

    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()

    mock_execute.return_value = {
        "items": [
            {
                "kind": "customsearch#result",
                "title": "Example",
                "snippet": "Snippet",
                "link": "https://example.com",
                "displayLink": "example.com",
            }
        ]
    }
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse

    with patch("src.tools.google_search_tool.build", return_value=mock_client):
        tool = GoogleSearchTool.from_settings(test_settings)
        results = tool._run("test query", num=1)

    assert len(results) == 1
    assert results[0]["platform"] == "google_search"
