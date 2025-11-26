# src/twitter_tool.py
import time
import logging
from datetime import datetime
from typing import List, Optional
from src.twitter_api_wrapper import TwitterAPIWrapper, NormalizedTweet

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def search_twitter(
    query: str,
    hashtags: Optional[List[str]] = None,
    language: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    max_results: int = 20
) -> List[NormalizedTweet]:

    wrapper = TwitterAPIWrapper()

    retries = 0
    max_retries = 5
    delay = 1
    backoff_factor = 2

    while retries <= max_retries:
        try:
            logger.info(f"Searching Twitter: '{query}' (retry {retries})")
            tweets = wrapper.search_tweets(
                query=query,
                max_results=max_results,
                hashtags=hashtags,
                language=language,
                start_time=start_time,
                end_time=end_time
            )
            logger.info(f"Retrieved {len(tweets)} tweets for query '{query}'")
            return tweets

        except Exception as e:
            logger.warning(f"Twitter API call failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= backoff_factor
            retries += 1

    logger.error(f"Twitter search failed after {max_retries} retries for query '{query}'")
    return []
