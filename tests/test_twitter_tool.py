# tests/test_twitter_tool.py
import pytest
from unittest.mock import patch
from src.twitter_tool import search_twitter
from src.twitter_api_wrapper import NormalizedTweet

@pytest.fixture
def mock_tweets():
    return [
        NormalizedTweet(
            text="Test tweet",
            author_handle="user1",
            permalink="https://twitter.com/i/web/status/1",
            created_at=None,
            like_count=1,
            repost_count=0,
            reply_count=0,
            language="en"
        )
    ]

def test_search_twitter_success(mock_tweets):
    with patch("src.twitter_tool.TwitterAPIWrapper") as MockWrapper:
        instance = MockWrapper.return_value
        instance.search_tweets.return_value = mock_tweets
        result = search_twitter("test query")
        assert len(result) == 1
        assert result[0].text == "Test tweet"

def test_search_twitter_zero_results():
    with patch("src.twitter_tool.TwitterAPIWrapper") as MockWrapper:
        instance = MockWrapper.return_value
        instance.search_tweets.return_value = []
        result = search_twitter("no results query")
        assert result == []

def test_search_twitter_auth_failure():
    with patch("src.twitter_tool.TwitterAPIWrapper.__init__", side_effect=ValueError("Missing credentials")):
        import pytest
        with pytest.raises(ValueError):
            search_twitter("test query")

def test_search_twitter_rate_limit_retry(mock_tweets, caplog):
    with patch("src.twitter_tool.TwitterAPIWrapper.search_tweets", side_effect=[Exception("Rate limit"), mock_tweets]):
        result = search_twitter("retry query", max_results=1)
        assert result == mock_tweets
        assert any("Retrying" in r.message for r in caplog.records)
