# src/twitter_api_wrapper.py

from dataclasses import dataclass
from typing import Protocol, List, Optional
from datetime import datetime
import logging
from config.settings import api_settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dataclass
class NormalizedTweet:
    text: str
    author_handle: str
    permalink: str
    created_at: Optional[datetime]
    like_count: int
    repost_count: int
    reply_count: int
    language: str

class TwitterAPIWrapperInterface(Protocol):
    def search_tweets(
        self,
        query: str,
        hashtags: Optional[List[str]] = None,
        language: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 20
    ) -> List[NormalizedTweet]:
        ...

class TwitterAPIWrapper:
    def __init__(self):
        if not api_settings.get("bearer_token"):
            raise ValueError("Missing Twitter bearer token in settings.api")
        self.bearer_token = api_settings["bearer_token"]
        # Could initialize Tweepy client here

    def search_tweets(self, query, hashtags=None, language=None, start_time=None, end_time=None, max_results=20):
        """
        Placeholder implementation; returns empty list
        Real implementation uses Tweepy to query Twitter API.
        """
        logger.info(f"Searching tweets: query={query}, hashtags={hashtags}, language={language}")
        return []
