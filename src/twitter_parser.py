# src/twitter_parser.py

import re
import logging
from typing import List, Dict
from datetime import timezone
from src.twitter_api_wrapper import NormalizedTweet

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

URL_PATTERN = re.compile(r"https?://\S+")
MARKDOWN_UNSAFE = re.compile(r"[*_~`>|\\]")

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    sanitized = URL_PATTERN.sub("", text)
    sanitized = MARKDOWN_UNSAFE.sub("", sanitized)
    sanitized = re.sub(r"\S+@\S+\.\S+", "[REDACTED_EMAIL]", sanitized)
    sanitized = re.sub(r"\+?\d[\d\s\-]{7,}", "[REDACTED_PHONE]", sanitized)
    return sanitized.strip()

def parse_tweets(raw_tweets: List[NormalizedTweet]) -> List[Dict]:
    seen_ids = set()
    parsed = []

    for tweet in raw_tweets:
        tweet_id = tweet.permalink.split("/")[-1]
        if tweet_id in seen_ids:
            logger.info(f"Duplicate tweet skipped: {tweet_id}")
            continue
        seen_ids.add(tweet_id)

        if not tweet.text or tweet.text.strip() == "":
            logger.info(f"Skipping tweet with missing text: {tweet_id}")
            continue

        clean_text = sanitize_text(tweet.text)
        timestamp = tweet.created_at.astimezone(timezone.utc).isoformat() if tweet.created_at else None

        parsed_tweet = {
            "id": tweet_id,
            "text": clean_text,
            "author_handle": tweet.author_handle,
            "url": tweet.permalink,
            "timestamp": timestamp,
            "like_count": tweet.like_count,
            "repost_count": tweet.repost_count,
            "reply_count": tweet.reply_count,
            "language": tweet.language,
            "platform": "twitter"
        }
        parsed.append(parsed_tweet)
    return parsed
