# twitter_wrapper.py
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Any
import twitter_tool

# ----------------------------
# DATA MODELS
# ----------------------------
@dataclass
class NormalizedTweet:
    id: str
    text: str
    author_username: Optional[str]
    created_at: str
    like_count: int = 0
    repost_count: int = 0
    reply_count: int = 0
    raw: Optional[Any] = None

@dataclass
class TweetPage:
    tweets: List[NormalizedTweet]
    next_cursor: Optional[str] = None

# ----------------------------
# WRAPPER IMPLEMENTATION
# ----------------------------
class TwitterWrapper:
    """
    Wrapper that uses twitter_tool to fetch tweets and normalize them.
    """

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token

    async def search_recent_tweets(self, query: str, max_results: int = 10) -> TweetPage:
        loop = asyncio.get_event_loop()
        raw_tweets = await loop.run_in_executor(
            None,
            lambda: twitter_tool.search_tweets(query, self.bearer_token, max_results)
        )
        tweets = [
            NormalizedTweet(
                id=t["id"],
                text=t["text"],
                author_username=t.get("author_id"),
                created_at=t["created_at"],
                raw=t
            )
            for t in raw_tweets
        ]
        return TweetPage(tweets=tweets)
