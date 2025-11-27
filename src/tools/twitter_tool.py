"""Twitter data retrieval tool for the pain point agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import tweepy
from langchain.tools import BaseTool

from config.settings import Settings


@dataclass
class NormalizedTweet:
    """Normalized tweet data structure."""

    text: str
    author_handle: str
    permalink: str
    created_timestamp: str  # ISO format
    like_count: int
    repost_count: int
    reply_count: int
    language: str

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "author_handle": self.author_handle,
            "permalink": self.permalink,
            "created_timestamp": self.created_timestamp,
            "like_count": self.like_count,
            "repost_count": self.repost_count,
            "reply_count": self.reply_count,
            "language": self.language,
        }


class TwitterAPIWrapper:
    """Wrapper for Twitter API v2 with authentication, rate limiting, and pagination."""

    def __init__(self, bearer_token: str):
        self.client = tweepy.Client(bearer_token=bearer_token)

    def search_tweets(
        self,
        query: str,
        max_results: int = 10,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        lang: Optional[str] = None,
        next_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search tweets with pagination and query parameters.

        Args:
            query: Search query (supports hashtags, keywords, etc.)
            max_results: Maximum results per request (10-100)
            start_time: Start time in ISO 8601 format
            end_time: End time in ISO 8601 format
            lang: Language code (e.g., 'en')
            next_token: Token for pagination

        Returns:
            Dict with 'tweets' list and 'next_token' if available
        """
        # Build query
        full_query = query
        if lang:
            full_query += f" lang:{lang}"

        # Convert times to datetime if provided
        start_dt = None
        end_dt = None
        if start_time:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        response = self.client.search_recent_tweets(
            query=full_query,
            max_results=min(max_results, 100),
            start_time=start_dt,
            end_time=end_dt,
            next_token=next_token,
            tweet_fields=["created_at", "public_metrics", "lang", "text", "author_id"],
            user_fields=["username"],
            expansions=["author_id"]
        )

        tweets = []
        users = {}
        if response.data:
            tweets = response.data
            if response.includes and "users" in response.includes:
                users = {user.id: user for user in response.includes["users"]}

        return {
            "tweets": tweets,
            "users": users,
            "next_token": response.meta.get("next_token") if response.meta else None
        }

    def normalize_tweet(self, tweet: tweepy.Tweet, users: Dict[str, tweepy.User]) -> NormalizedTweet:
        """Normalize raw tweet data to our schema."""
        author = users.get(tweet.author_id)
        author_handle = author.username if author else ""

        return NormalizedTweet(
            text=tweet.text,
            author_handle=author_handle,
            permalink=f"https://twitter.com/{author_handle}/status/{tweet.id}",
            created_timestamp=tweet.created_at.isoformat() if tweet.created_at else "",
            like_count=tweet.public_metrics.get("like_count", 0) if tweet.public_metrics else 0,
            repost_count=tweet.public_metrics.get("retweet_count", 0) if tweet.public_metrics else 0,
            reply_count=tweet.public_metrics.get("reply_count", 0) if tweet.public_metrics else 0,
            language=tweet.lang or ""
        )


class TwitterTool(BaseTool):
    """Fetches relevant Twitter posts based on a user query."""

    name = "twitter_search"
    description = "Search Twitter for discussions related to customer pain points. Supports hashtags, keywords, language filters, and time windows."

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.wrapper = TwitterAPIWrapper(settings.api.twitter_api_key)

    @classmethod
    def from_settings(cls, settings: Settings) -> "TwitterTool":
        """Factory method to create a tool instance from global settings."""
        return cls(settings)

    def _run(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Synchronously execute the tool and return search results."""
        response = self.wrapper.search_tweets(
            query=query,
            max_results=kwargs.get("max_results", 10),
            start_time=kwargs.get("start_time"),
            end_time=kwargs.get("end_time"),
            lang=kwargs.get("lang")
        )

        normalized_tweets = [
            self.wrapper.normalize_tweet(tweet, response["users"]).dict()
            for tweet in response["tweets"]
        ]

        return normalized_tweets

    async def _arun(
        self,
        query: str,
        max_results: int = 10,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        lang: Optional[str] = None,
        *args: Any,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Asynchronously execute the tool and return search results.

        Args:
            query: Search query
            max_results: Number of results to fetch
            start_time: ISO 8601 start time
            end_time: ISO 8601 end time
            lang: Language code

        Returns:
            List of normalized tweet dictionaries
        """
        # For simplicity, since tweepy is sync, run in thread
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self.wrapper.search_tweets, query, max_results, start_time, end_time, lang, None)

        normalized_tweets = [
            self.wrapper.normalize_tweet(tweet, response["users"]).dict()
            for tweet in response["tweets"]
        ]

        return normalized_tweets
