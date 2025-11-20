"""
Twitter API Wrapper Interface Specification

Defines:
- NormalizedTweet: Unified tweet model.
- TweetPage: Pagination wrapper.
- TwitterApiWrapper: Typed interface with documented methods and return schemas.

This file is implementation-agnostic.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Protocol, Any, Dict


# ----------------------------
# DATA MODELS
# ----------------------------
@dataclass
class NormalizedTweet:
    """
    Normalized representation of a Tweet.

    Fields:
    - id: Unique tweet ID
    - text: Full tweet text
    - author_username: Handle of the author (without '@')
    - permalink: Public URL to the tweet
    - created_at: ISO 8601 timestamp
    - like_count: Number of likes
    - repost_count: Number of retweets/reposts
    - reply_count: Number of replies
    - language: BCP-47 language code
    - raw: Provider-specific payload
    """
    id: str
    text: str
    author_username: Optional[str]
    permalink: Optional[str]
    created_at: str
    like_count: int
    repost_count: int
    reply_count: int
    language: Optional[str] = None
    raw: Optional[Any] = None


@dataclass
class TweetPage:
    """Container for paginated tweets"""
    tweets: List[NormalizedTweet]
    next_cursor: Optional[str] = None


# ----------------------------
# INTERFACE CONTRACT
# ----------------------------
class TwitterApiWrapper(Protocol):
    """
    Provider-agnostic interface for fetching normalized tweets.

    Authentication:
    - Bearer token or OAuth2 credentials loaded from config.settings

    Pagination:
    - Implementations must normalize provider-specific cursor tokens into `next_cursor`

    Query Parameters:
    - Supports hashtags, language, time window filters
    """

    async def get_tweet_by_id(self, tweet_id: str) -> Optional[NormalizedTweet]:
        """Fetch a single tweet by ID"""
        ...

    async def get_tweets_by_ids(self, tweet_ids: List[str]) -> List[NormalizedTweet]:
        """Fetch multiple tweets by their IDs"""
        ...

    async def search_recent_tweets(
        self,
        query: str,
        *,
        max_results: int = 50,
        next_cursor: Optional[str] = None,
        lang: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> TweetPage:
        """Search recent tweets using query and optional filters"""
        ...

    async def get_user_timeline(
        self,
        user_id: str,
        *,
        max_results: int = 50,
        next_cursor: Optional[str] = None,
        exclude_replies: bool = False,
        exclude_reposts: bool = False,
    ) -> TweetPage:
        """Fetch a user's timeline"""
        ...

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Lookup a user by username"""
        ...

    async def raw_request(self, endpoint: str, params: Dict[str, Any]) -> Any:
        """Low-level escape hatch for provider-specific API calls"""
        ...
