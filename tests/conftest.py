# tests/conftest.py
import pytest
from datetime import datetime
from src.twitter_api_wrapper import NormalizedTweet

@pytest.fixture
def sample_tweets():
    """
    Returns a list of anonymized NormalizedTweet objects
    covering varied metadata and edge cases.
    """
    return [
        NormalizedTweet(
            text="Hello world! Visit https://example.com",
            author_handle="user123",
            permalink="https://twitter.com/i/web/status/1",
            created_at=datetime(2025, 1, 1, 12, 0),
            like_count=10,
            repost_count=2,
            reply_count=1,
            language="en"
        ),
        NormalizedTweet(
            text="",  # media-only / empty tweet
            author_handle="user456",
            permalink="https://twitter.com/i/web/status/2",
            created_at=datetime(2025, 1, 2, 15, 0),
            like_count=5,
            repost_count=0,
            reply_count=0,
            language="en"
        ),
        NormalizedTweet(
            text="Duplicate tweet test",
            author_handle="user123",
            permalink="https://twitter.com/i/web/status/1",
            created_at=datetime(2025, 1, 1, 12, 0),
            like_count=10,
            repost_count=2,
            reply_count=1,
            language="en"
        )
    ]
