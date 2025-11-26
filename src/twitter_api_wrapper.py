# src/twitter_api_wrapper.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol
import tweepy
from config.api_settings import TWITTER_BEARER_TOKEN

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
        max_results: int = 20,
        hashtags: Optional[list] = None,
        language: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[NormalizedTweet]:
        ...

class TwitterAPIWrapper(TwitterAPIWrapperInterface):
    def __init__(self):
        if not TWITTER_BEARER_TOKEN:
            raise ValueError("Twitter API credentials missing in config.api_settings")
        self.client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=True)

    def search_tweets(
        self,
        query: str,
        max_results: int = 20,
        hashtags: Optional[list] = None,
        language: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[NormalizedTweet]:
        if hashtags:
            query += " " + " ".join(f"#{tag}" for tag in hashtags)

        tweets: List[NormalizedTweet] = []
        try:
            for response in tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                tweet_fields=['created_at','public_metrics','lang','author_id'],
                max_results=100,
                start_time=start_time,
                end_time=end_time
            ):
                for t in response.data or []:
                    nt = NormalizedTweet(
                        text=t.text,
                        author_handle=str(t.author_id),
                        permalink=f"https://twitter.com/i/web/status/{t.id}",
                        created_at=t.created_at,
                        like_count=t.public_metrics.get('like_count',0),
                        repost_count=t.public_metrics.get('retweet_count',0),
                        reply_count=t.public_metrics.get('reply_count',0),
                        language=t.lang
                    )
                    tweets.append(nt)
                    if len(tweets) >= max_results:
                        return tweets
        except Exception as e:
            raise RuntimeError(f"Twitter API error: {e}")

        return tweets
