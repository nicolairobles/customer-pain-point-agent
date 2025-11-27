import json
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, ConfigDict

from src.tools.twitter_tool import TwitterTool, NormalizedTweet


class DummyTweet:
    def __init__(
        self,
        id,
        text,
        created_at,
        author_id,
        public_metrics=None,
        lang="en"
    ):
        self.id = id
        self.text = text
        self.created_at = created_at
        self.author_id = author_id
        self.public_metrics = public_metrics or {
            "like_count": 10,
            "retweet_count": 5,
            "reply_count": 2
        }
        self.lang = lang


class DummyUser:
    def __init__(self, id, username):
        self.id = id
        self.username = username


class DummyResponse:
    def __init__(self, tweets, users, next_token=None):
        self.data = tweets
        self.includes = {"users": users} if users else None
        self.meta = {"next_token": next_token} if next_token else None


@pytest.fixture
def settings():
    class S:
        class API:
            twitter_api_key = "dummy_bearer_token"

        api = API()

    return S()


def test_twitter_tool_returns_normalized_results(monkeypatch, settings):
    # Create dummy tweets
    tweets = [
        DummyTweet(
            "1234567890",
            "Having issues with customer service response times #frustrated",
            "2024-01-15T10:30:00.000Z",
            "user1",
            {"like_count": 25, "retweet_count": 5, "reply_count": 8},
            "en"
        ),
        DummyTweet(
            "1234567891",
            "Great support from @company today!",
            "2024-01-15T11:00:00.000Z",
            "user2",
            {"like_count": 15, "retweet_count": 3, "reply_count": 1},
            "en"
        )
    ]

    users = [
        DummyUser("user1", "customer123"),
        DummyUser("user2", "happyuser")
    ]

    response = DummyResponse(tweets, users)

    # Mock the tweepy client
    mock_client = MagicMock()
    mock_client.search_recent_tweets.return_value = response

    monkeypatch.setattr("src.tools.twitter_tool.tweepy.Client", lambda bearer_token: mock_client)

    tool = TwitterTool.from_settings(settings)
    results = tool._run("customer service", max_results=10)

    assert isinstance(results, list)
    assert len(results) == 2

    # Check first tweet normalization
    tweet1 = results[0]
    assert tweet1["text"] == "Having issues with customer service response times #frustrated"
    assert tweet1["author_handle"] == "customer123"
    assert tweet1["permalink"] == "https://twitter.com/customer123/status/1234567890"
    assert tweet1["created_timestamp"] == "2024-01-15T10:30:00+00:00"
    assert tweet1["like_count"] == 25
    assert tweet1["repost_count"] == 5
    assert tweet1["reply_count"] == 8
    assert tweet1["language"] == "en"

    # Check second tweet normalization
    tweet2 = results[1]
    assert tweet2["text"] == "Great support from @company today!"
    assert tweet2["author_handle"] == "happyuser"
    assert tweet2["permalink"] == "https://twitter.com/happyuser/status/1234567891"
    assert tweet2["created_timestamp"] == "2024-01-15T11:00:00+00:00"
    assert tweet2["like_count"] == 15
    assert tweet2["repost_count"] == 3
    assert tweet2["reply_count"] == 1
    assert tweet2["language"] == "en"


def test_twitter_tool_handles_empty_results(monkeypatch, settings):
    # Mock empty response
    response = DummyResponse([], None)

    mock_client = MagicMock()
    mock_client.search_recent_tweets.return_value = response

    monkeypatch.setattr("src.tools.twitter_tool.tweepy.Client", lambda bearer_token: mock_client)

    tool = TwitterTool.from_settings(settings)
    results = tool._run("nonexistent query")

    assert results == []


def test_twitter_tool_handles_api_errors(monkeypatch, settings):
    # Mock API error
    mock_client = MagicMock()
    mock_client.search_recent_tweets.side_effect = Exception("API rate limit exceeded")

    monkeypatch.setattr("src.tools.twitter_tool.tweepy.Client", lambda bearer_token: mock_client)

    tool = TwitterTool.from_settings(settings)

    # Should raise exception (unlike Reddit tool which returns empty list)
    with pytest.raises(Exception, match="API rate limit exceeded"):
        tool._run("test query")


def test_normalized_tweet_dict_method():
    """Test that NormalizedTweet.dict() returns correct dictionary."""
    tweet = NormalizedTweet(
        text="Test tweet",
        author_handle="testuser",
        permalink="https://twitter.com/testuser/status/123",
        created_timestamp="2024-01-15T10:30:00.000Z",
        like_count=10,
        repost_count=5,
        reply_count=2,
        language="en"
    )

    expected = {
        "text": "Test tweet",
        "author_handle": "testuser",
        "permalink": "https://twitter.com/testuser/status/123",
        "created_timestamp": "2024-01-15T10:30:00.000Z",
        "like_count": 10,
        "repost_count": 5,
        "reply_count": 2,
        "language": "en"
    }

    assert tweet.dict() == expected


def test_twitter_tool_with_query_parameters(monkeypatch, settings):
    """Test that query parameters are passed correctly to the API."""
    tweets = [DummyTweet("123", "Test", "2024-01-15T10:30:00.000Z", "user1")]
    users = [DummyUser("user1", "testuser")]
    response = DummyResponse(tweets, users)

    mock_client = MagicMock()
    mock_client.search_recent_tweets.return_value = response

    monkeypatch.setattr("src.tools.twitter_tool.tweepy.Client", lambda bearer_token: mock_client)

    tool = TwitterTool.from_settings(settings)
    results = tool._run(
        "test query",
        max_results=5,
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-02T00:00:00Z",
        lang="en"
    )

    # Verify the call was made with correct parameters
    mock_client.search_recent_tweets.assert_called_once()
    call_args = mock_client.search_recent_tweets.call_args

    assert call_args[1]["query"] == "test query lang:en"
    assert call_args[1]["max_results"] == 5
    # start_time and end_time would be datetime objects after conversion

    assert len(results) == 1


def test_twitter_tool_async_run(monkeypatch, settings):
    """Test the async _arun method."""
    import asyncio

    tweets = [DummyTweet("123", "Async test", "2024-01-15T10:30:00.000Z", "user1")]
    users = [DummyUser("user1", "testuser")]
    response = DummyResponse(tweets, users)

    mock_client = MagicMock()
    mock_client.search_recent_tweets.return_value = response

    monkeypatch.setattr("src.tools.twitter_tool.tweepy.Client", lambda bearer_token: mock_client)

    tool = TwitterTool.from_settings(settings)

    async def run_test():
        results = await tool._arun("async query", max_results=5)
        assert len(results) == 1
        assert results[0]["text"] == "Async test"

    asyncio.run(run_test())

    async def run_test():
        results = await tool._arun("async query", max_results=5)
        assert len(results) == 1
        assert results[0]["text"] == "Async test"

    asyncio.run(run_test())