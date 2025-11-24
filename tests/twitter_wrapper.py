import asyncio
from dataclasses import dataclass
from typing import List, Optional, Any
from datetime import datetime
import re
from collections import deque
import logging
import twitter_tool

# ----------------------------
# SETUP LOGGER
# ----------------------------
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ----------------------------
# DATA MODELS
# ----------------------------
@dataclass
class NormalizedTweet:
    id: str
    text: str
    author_username: Optional[str]
    created_at: Optional[str]
    like_count: int = 0
    repost_count: int = 0
    reply_count: int = 0
    language: Optional[str] = None
    permalink: Optional[str] = None
    platform: str = "twitter"
    raw: Optional[Any] = None


@dataclass
class TweetPage:
    tweets: List[NormalizedTweet]
    next_cursor: Optional[str] = None


# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def clean_text(text: str) -> str:
    """Remove URLs, markdown-unsafe characters, and basic PII placeholders."""
    text = re.sub(r'https?://\S+', '', text)  # Remove URLs
    text = text.replace('*', '').replace('_', '').replace('`', '')  # Remove markdown-unsafe chars
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', '[email]', text)  # Remove emails
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[phone]', text)  # Remove phone numbers
    return text.strip()


def isoformat_utc(timestamp: str) -> str:
    """Convert Twitter timestamp to ISO 8601 UTC."""
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return dt.astimezone().isoformat()


# ----------------------------
# WRAPPER IMPLEMENTATION
# ----------------------------
class TwitterWrapper:
    """Wrapper that uses twitter_tool to fetch and parse tweets with bounded deduplication."""

    def __init__(self, bearer_token: str, cache_size: int = 1000):
        self.bearer_token = bearer_token
        self.seen_ids = deque(maxlen=cache_size)  # bounded cache for deduplication

    def clear_cache(self):
        """Clear the set of seen tweet IDs."""
        self.seen_ids.clear()

    async def search_recent_tweets(self, query: str, max_results: int = 10) -> TweetPage:
        loop = asyncio.get_event_loop()

        raw_tweets = await loop.run_in_executor(
            None,
            lambda: twitter_tool.search_tweets(query, self.bearer_token, max_results)
        )

        tweets: List[NormalizedTweet] = []
        request_seen_ids = set()  # per-request deduplication

        for t in raw_tweets:
            tweet_id = t.get("id")
            if not tweet_id:
                continue  # skip if no ID

            # Skip duplicates (both cache and current request)
            if tweet_id in self.seen_ids or tweet_id in request_seen_ids:
                continue

            request_seen_ids.add(tweet_id)
            self.seen_ids.append(tweet_id)

            # Skip tweets with no text
            text = t.get("text")
            if not text:
                continue

            cleaned_text = clean_text(text)

            # Build permalink
            author_id = t.get("author_id")
            permalink = f"https://twitter.com/{author_id}/status/{tweet_id}" if author_id else None

            # Convert timestamp to ISO 8601 UTC with logging for failures
            created_at = None
            raw_timestamp = t.get("created_at")
            if raw_timestamp:
                try:
                    created_at = isoformat_utc(raw_timestamp)
                except (ValueError, KeyError) as e:
                    logger.warning(
                        "Failed to parse timestamp for tweet id %s: %s. Using raw timestamp.",
                        tweet_id,
                        e
                    )
                    created_at = raw_timestamp

            tweet = NormalizedTweet(
                id=tweet_id,
                text=cleaned_text,
                author_username=author_id,
                created_at=created_at,
                permalink=permalink,
                platform="twitter",
                raw=t
            )

            tweets.append(tweet)

        return TweetPage(tweets=tweets)