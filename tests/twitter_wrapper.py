import asyncio
from dataclasses import dataclass
from typing import List, Optional, Any
from datetime import datetime
import re
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
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove markdown-unsafe characters
    text = text.replace('*', '').replace('_', '').replace('`', '')
    # Basic PII removal (emails, phone numbers)
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', '[email]', text)
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[phone]', text)
    return text.strip()


def isoformat_utc(timestamp: str) -> str:
    """Convert Twitter timestamp to ISO 8601 UTC."""
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return dt.astimezone().isoformat()


# ----------------------------
# WRAPPER IMPLEMENTATION
# ----------------------------
class TwitterWrapper:
    """Wrapper that uses twitter_tool to fetch and parse tweets."""

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.seen_ids = set()  # For deduplication

    async def search_recent_tweets(self, query: str, max_results: int = 10) -> TweetPage:
        loop = asyncio.get_event_loop()

        raw_tweets = await loop.run_in_executor(
            None,
            lambda: twitter_tool.search_tweets(query, self.bearer_token, max_results)
        )

        tweets: List[NormalizedTweet] = []

        for t in raw_tweets:
            # Skip duplicates
            if t["id"] in self.seen_ids:
                continue
            self.seen_ids.add(t["id"])

            # Skip tweets with no text
            text = t.get("text")
            if not text:
                continue

            cleaned_text = clean_text(text)

            # Build permalink
            author_id = t.get("author_id")
            permalink = f"https://twitter.com/{author_id}/status/{t['id']}" if author_id else None

            # Convert timestamp to ISO 8601 UTC
            try:
                created_at = isoformat_utc(t["created_at"])
            except Exception:
                created_at = t["created_at"]  # fallback if malformed

            tweet = NormalizedTweet(
                id=t["id"],
                text=cleaned_text,
                author_username=author_id,
                created_at=created_at,
                permalink=permalink,
                platform="twitter",
                raw=t
            )

            tweets.append(tweet)

        return TweetPage(tweets=tweets)
