# src/twitter_tool.py

import time
import logging
from typing import List, Optional
from src.twitter_api_wrapper import TwitterAPIWrapper, NormalizedTweet

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def search_twitter(
    query: str,
    hashtags: Optional[List[str]] = None,
    language: Optional[str] = None,
    start_time=None,
    end_time=None,
    max_results: int = 20
) -> List[NormalizedTweet]:
    try:
        wrapper = TwitterAPIWrapper()
    except ValueError as e:
        logger.error(f"Authentication error: {e}")
        raise

    retries = 0
    while retries < 5:
        try:
            tweets = wrapper.search_tweets(query, hashtags, language, start_time, end_time, max_results)
            return tweets
        except Exception as e:
            retries += 1
            wait_time = 2 ** retries
            logger.warning(f"Rate limit or API error. Retry {retries}/5 after {wait_time}s")
            time.sleep(wait_time)
    return []
