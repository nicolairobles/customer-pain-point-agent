# tests/twitter/test_twitter_wrapper.py

import sys
from pathlib import Path
import pytest
from unittest.mock import patch
import asyncio
from datetime import datetime

# ----------------------------
# Fix imports: add tests/ folder to sys.path
# ----------------------------
project_root = Path(__file__).resolve().parents[1]  # goes up to tests/
sys.path.insert(0, str(project_root))

# ----------------------------
# Imports
# ----------------------------
from twitter_wrapper import TwitterWrapper, NormalizedTweet, TweetPage

# ----------------------------
# Sample anonymized tweets fixture
# ----------------------------
@pytest.fixture
def sample_raw_tweets():
    return [
        {
            "id": "111",
            "text": "Hello Twitter!",
            "author_id": "999",
            "created_at": "2025-11-20T12:00:00.000Z"
        },
        {
            "id": "222",
            "text": "Another tweet example",
            "author_id": "888",
            "created_at": "2025-11-20T12:01:00.000Z"
        }
    ]

# ----------------------------
# Test wrapper returns normalized tweets
# ----------------------------
def test_wrapper_normalizes(sample_raw_tweets):
    # Patch twitter_tool.search_tweets to return our fixture data
    with patch("twitter_wrapper.twitter_tool.search_tweets", return_value=sample_raw_tweets):
        wrapper = TwitterWrapper("FAKE_TOKEN")
        page: TweetPage = asyncio.run(wrapper.search_recent_tweets("test query", max_results=2))

        # Assertions
        assert isinstance(page, TweetPage)
        assert len(page.tweets) == 2

        for tweet in page.tweets:
            assert isinstance(tweet, NormalizedTweet)
            assert tweet.id in {"111", "222"}
            assert tweet.text != ""
            assert tweet.author_username in {"999", "888"}
            # ISO 8601 timestamp
            datetime.fromisoformat(tweet.created_at)
            assert tweet.raw is not None

# ----------------------------
# Test empty results
# ----------------------------
def test_wrapper_empty_results():
    with patch("twitter_wrapper.twitter_tool.search_tweets", return_value=[]):
        wrapper = TwitterWrapper("FAKE_TOKEN")
        page: TweetPage = asyncio.run(wrapper.search_recent_tweets("nothing", max_results=2))
        assert isinstance(page, TweetPage)
        assert len(page.tweets) == 0
