# tests/test_twitter_api_wrapper.py
import sys
from pathlib import Path

# Add project src folder to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import pytest
from datetime import datetime
from src.twitter_api_wrapper import NormalizedTweet, TwitterAPIWrapper, TwitterAPIWrapperInterface
from unittest.mock import patch

def test_normalized_tweet_fields():
    """Ensure NormalizedTweet dataclass has all required fields."""
    tweet = NormalizedTweet(
        text="Hello world",
        author_handle="user123",
        permalink="https://twitter.com/i/web/status/1",
        created_at=datetime(2025, 1, 1, 12, 0),
        like_count=5,
        repost_count=2,
        reply_count=1,
        language="en"
    )

    assert tweet.text == "Hello world"
    assert tweet.author_handle == "user123"
    assert tweet.permalink == "https://twitter.com/i/web/status/1"
    assert isinstance(tweet.created_at, datetime)
    assert tweet.like_count == 5
    assert tweet.repost_count == 2
    assert tweet.reply_count == 1
    assert tweet.language == "en"

def test_interface_method_signature():
    """Check that TwitterAPIWrapperInterface defines search_tweets."""
    assert hasattr(TwitterAPIWrapperInterface, "search_tweets")

def test_wrapper_init_with_credentials():
    """Ensure TwitterAPIWrapper initializes with credentials."""
    with patch("twitter_api_wrapper.TWITTER_BEARER_TOKEN", "fake-token"):
        wrapper = TwitterAPIWrapper()
        assert hasattr(wrapper, "search_tweets")

def test_wrapper_init_missing_credentials():
    """Ensure TwitterAPIWrapper raises error if credentials missing."""
    with patch("twitter_api_wrapper.TWITTER_BEARER_TOKEN", None):
        import pytest
        with pytest.raises(ValueError):
            TwitterAPIWrapper()
