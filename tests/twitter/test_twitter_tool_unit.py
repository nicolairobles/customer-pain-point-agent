# tests/twitter/test_twitter_tool_unit.py

import sys
from pathlib import Path
import pytest
from unittest.mock import patch, Mock
import logging
import requests

# ----------------------------
# Fix imports: add tests/ folder to sys.path
# ----------------------------
project_root = Path(__file__).resolve().parents[1]  # goes up to tests/
sys.path.insert(0, str(project_root))

# ----------------------------
# Imports
# ----------------------------
from twitter_tool import search_tweets, retry_request
from twitter_wrapper import TwitterWrapper

# ----------------------------
# Sample anonymized tweets fixture
# ----------------------------
@pytest.fixture
def sample_tweets():
    return {
        "data": [
            {
                "id": "12345",
                "text": "Hello world! Check https://t.co/test",
                "author_id": "999",
                "created_at": "2025-11-20T12:00:00.000Z"
            },
            {
                "id": "12346",
                "text": "Another tweet",
                "author_id": "888",
                "created_at": "2025-11-20T12:01:00.000Z"
            }
        ]
    }

# ----------------------------
# Test success response
# ----------------------------
@patch("requests.get")
def test_search_tweets_success(mock_get, sample_tweets):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_tweets
    mock_get.return_value = mock_response

    tweets = search_tweets("test query", "FAKE_TOKEN", max_results=2)
    assert len(tweets) == 2
    assert tweets[0]["id"] == "12345"
    assert tweets[1]["text"] == "Another tweet"

# ----------------------------
# Test zero-result response
# ----------------------------
@patch("requests.get")
def test_search_tweets_zero_results(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}  # no "data" field
    mock_get.return_value = mock_response

    tweets = search_tweets("nothingmatches", "FAKE_TOKEN")
    assert tweets == []

# ----------------------------
# Test rate-limit (HTTP 429) handling
# ----------------------------
@patch("requests.get")
def test_retry_on_rate_limit(mock_get):
    mock_response_429 = Mock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"x-rate-limit-reset": "0"}  # immediate retry

    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"data": []}

    mock_get.side_effect = [mock_response_429, mock_response_200]

    with patch("time.sleep") as mock_sleep:
        result = retry_request("http://fakeurl", {}, {})
        mock_sleep.assert_called()
        assert result == {"data": []}

# ----------------------------
# Test authentication failure
# ----------------------------
@patch("requests.get")
def test_auth_failure_raises(mock_get):
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    # Ensure raise_for_status() raises HTTPError
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Client Error")
    mock_get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        retry_request("http://fakeurl", {}, {})

# ----------------------------
# Test malformed payload
# ----------------------------
@patch("requests.get")
def test_malformed_payload_raises(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Malformed JSON")
    mock_get.return_value = mock_response

    with pytest.raises(ValueError):
        search_tweets("test query", "FAKE_TOKEN")

# ----------------------------
# Test wrapper parsing logic
# ----------------------------
def test_wrapper_parsing(sample_tweets):
    # Patch twitter_tool.search_tweets to return fixture data
    with patch("twitter_wrapper.twitter_tool.search_tweets", return_value=sample_tweets["data"]):
        wrapper = TwitterWrapper("FAKE_TOKEN")
        import asyncio
        page = asyncio.run(wrapper.search_recent_tweets("test query", max_results=2))

        assert len(page.tweets) == 2
        for tweet in page.tweets:
            assert tweet.id in {"12345", "12346"}
            assert tweet.text != ""
            assert tweet.author_username in {"999", "888"}
            assert tweet.raw is not None
            from datetime import datetime
            # Ensure timestamps are ISO 8601
            datetime.fromisoformat(tweet.created_at)
