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
    assert tweet1["platform"] == "twitter"

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
    assert tweet2["platform"] == "twitter"


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
        "language": "en",
        "platform": "twitter"
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


def test_sanitize_text_function():
    """Test the sanitize_text function removes URLs, emails, phones, and markdown chars."""
    from src.tools.twitter_tool import sanitize_text
    
    # Test URL removal
    assert sanitize_text("Check this link: https://example.com") == "Check this link:"
    
    # Test email masking
    assert sanitize_text("Contact me at user@example.com") == "Contact me at [EMAIL]"
    
    # Test phone masking
    assert sanitize_text("Call me at 123-456-7890") == "Call me at [PHONE]"
    
    # Test markdown unsafe chars
    assert sanitize_text("Text with *bold* and |table|") == "Text with bold and table"
    
    # Test combination
    text = "Visit https://site.com or email test@example.com, call 555-123-4567, and see *this* |table|"
    expected = "Visit or email [EMAIL], call [PHONE], and see this table"
    assert sanitize_text(text) == expected
    
    # Test empty/whitespace
    assert sanitize_text("") == ""
    assert sanitize_text("   ") == ""
    assert sanitize_text(None) == ""


def test_normalize_tweet_skips_retweets():
    """Test that retweets are skipped during normalization."""
    from src.tools.twitter_tool import TwitterAPIWrapper
    
    # Create a mock retweet
    class MockRef:
        type = "retweeted"
    
    class MockTweet:
        id = "123"
        text = "RT @original: Original tweet"
        created_at = None
        author_id = "user1"
        public_metrics = {"like_count": 10, "retweet_count": 5, "reply_count": 2}
        lang = "en"
        referenced_tweets = [MockRef()]
    
    users = {"user1": MagicMock(username="testuser")}
    
    wrapper = TwitterAPIWrapper("dummy_token")
    result = wrapper.normalize_tweet(MockTweet(), users)
    
    assert result is None  # Should return None for retweets


def test_normalize_tweet_handles_missing_fields():
    """Test normalization handles missing author, empty text, etc."""
    from src.tools.twitter_tool import TwitterAPIWrapper
    
    wrapper = TwitterAPIWrapper("dummy_token")
    
    # Test missing author
    class MockTweet:
        id = "123"
        text = "Test tweet"
        created_at = None
        author_id = "user1"
        public_metrics = None
        lang = "en"
        referenced_tweets = None
    
    users = {}  # No users
    result = wrapper.normalize_tweet(MockTweet(), users)
    assert result is None
    
    # Test empty text
    class MockTweetEmpty:
        id = "124"
        text = ""
        created_at = None
        author_id = "user1"
        public_metrics = None
        lang = "en"
        referenced_tweets = None
    
    users = {"user1": MagicMock(username="testuser")}
    result = wrapper.normalize_tweet(MockTweetEmpty(), users)
    assert result is None
    
    # Test text that becomes empty after sanitization (only URLs)
    class MockTweetURLs:
        id = "125"
        text = "https://example.com https://another.com"
        created_at = None
        author_id = "user1"
        public_metrics = None
        lang = "en"
        referenced_tweets = None
    
    result = wrapper.normalize_tweet(MockTweetURLs(), users)
    assert result is None


def test_normalize_tweet_with_sanitization():
    """Test that tweet text is sanitized during normalization."""
    from src.tools.twitter_tool import TwitterAPIWrapper
    
    wrapper = TwitterAPIWrapper("dummy_token")
    
    class MockTweet:
        id = "123"
        text = "Check this https://example.com and email test@example.com *bold*"
        created_at = "2024-01-15T10:30:00.000Z"
        author_id = "user1"
        public_metrics = {"like_count": 10, "retweet_count": 5, "reply_count": 2}
        lang = "en"
        referenced_tweets = None
    
    users = {"user1": MagicMock(username="testuser")}
    result = wrapper.normalize_tweet(MockTweet(), users)
    
    assert result is not None
    assert result.text == "Check this and email [EMAIL] bold"
    assert result.platform == "twitter"


def test_normalize_tweet_utc_timestamp():
    """Test that timestamps are converted to UTC ISO format."""
    from src.tools.twitter_tool import TwitterAPIWrapper
    from datetime import datetime, timezone
    
    wrapper = TwitterAPIWrapper("dummy_token")
    
    # Test naive datetime (assume UTC)
    naive_dt = datetime(2024, 1, 15, 10, 30, 0)
    
    class MockTweet:
        id = "123"
        text = "Test tweet"
        created_at = naive_dt
        author_id = "user1"
        public_metrics = {"like_count": 10, "retweet_count": 5, "reply_count": 2}
        lang = "en"
        referenced_tweets = None
    
    users = {"user1": MagicMock(username="testuser")}
    result = wrapper.normalize_tweet(MockTweet(), users)
    
    assert result is not None
    assert result.created_timestamp == "2024-01-15T10:30:00+00:00"


def test_error_handling_malformed_payload():
    """Test that malformed payloads are handled gracefully."""
    from src.tools.twitter_tool import TwitterAPIWrapper
    
    wrapper = TwitterAPIWrapper("dummy_token")
    
    # Test tweet with missing attributes
    class MalformedTweet:
        pass  # No attributes
    
    users = {}
    result = wrapper.normalize_tweet(MalformedTweet(), users)
    assert result is None



def test_data_quality_schema_validation():
    """Test that normalized payloads satisfy the interface contract."""
    import json
    from src.tools.twitter_tool import TwitterAPIWrapper, NormalizedTweet
    
    # Define expected schema
    expected_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "author_handle": {"type": "string"},
            "permalink": {"type": "string"},
            "created_timestamp": {"type": "string"},
            "like_count": {"type": "integer"},
            "repost_count": {"type": "integer"},
            "reply_count": {"type": "integer"},
            "language": {"type": "string"},
            "platform": {"type": "string", "enum": ["twitter"]}
        },
        "required": ["text", "author_handle", "permalink", "created_timestamp", 
                    "like_count", "repost_count", "reply_count", "language", "platform"]
    }
    
    wrapper = TwitterAPIWrapper("dummy_token")
    
    class MockTweet:
        id = "123"
        text = "Valid tweet content"
        created_at = "2024-01-15T10:30:00.000Z"
        author_id = "user1"
        public_metrics = {"like_count": 10, "retweet_count": 5, "reply_count": 2}
        lang = "en"
        referenced_tweets = None
    
    users = {"user1": MagicMock(username="testuser")}
    result = wrapper.normalize_tweet(MockTweet(), users)
    
    assert result is not None
    
    # Convert to dict and validate against schema
    tweet_dict = result.dict()
    
    # Basic validation - check all required fields exist
    for field in expected_schema["required"]:
        assert field in tweet_dict, f"Missing required field: {field}"
    
    # Check types
    assert isinstance(tweet_dict["text"], str)
    assert isinstance(tweet_dict["author_handle"], str)
    assert isinstance(tweet_dict["permalink"], str)
    assert isinstance(tweet_dict["created_timestamp"], str)
    assert isinstance(tweet_dict["like_count"], int)
    assert isinstance(tweet_dict["repost_count"], int)
    assert isinstance(tweet_dict["reply_count"], int)
    assert isinstance(tweet_dict["language"], str)
    assert isinstance(tweet_dict["platform"], str)
    assert tweet_dict["platform"] == "twitter"
    
    # Check permalink format
    assert "twitter.com" in tweet_dict["permalink"]
    assert tweet_dict["permalink"].endswith("/status/123")
