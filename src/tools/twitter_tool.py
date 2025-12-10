from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import tweepy
from pydantic import PrivateAttr
from langchain.tools import BaseTool

from config.settings import Settings

# Set up logging
_LOG = logging.getLogger(__name__)

# Regex patterns for sanitization
_URL_RE = re.compile(r'https?://\S+')
_EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
_PHONE_RE = re.compile(
    r'\b(?:\+?\d{1,3}[\s\-\.]+)?(?:\(?\d{3}\)?[\s\-\.]+)?\d{3}[\s\-\.]+\d{4}\b'
)  # Improved phone number pattern: matches common formats, avoids dates by requiring at least one non-digit separator
_MARKDOWN_UNSAFE_RE = re.compile(r'[|*_`~]')  # Characters that might break markdown


def sanitize_text(raw_text: str) -> str:
    """Sanitize tweet text by removing URLs, PII, and markdown-unsafe characters."""
    if not raw_text:
        return ""
    
    text = str(raw_text)
    
    # Remove URLs
    text = _URL_RE.sub('', text)
    
    # Remove emails
    text = _EMAIL_RE.sub('[EMAIL]', text)  # Mask emails
    
    # Remove phone numbers
    text = _PHONE_RE.sub('[PHONE]', text)  # Mask phone numbers
    
    # Remove markdown-unsafe characters
    text = _MARKDOWN_UNSAFE_RE.sub('', text)
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


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
    platform: str = "twitter"  # Add platform field

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
            "platform": self.platform,  # Add to dict
        }


class TwitterAPIError(Exception):
    """Custom exception for Twitter API errors."""
    pass


class TwitterAPIWrapper:
    """Wrapper for Twitter API v2 with authentication, rate limiting, and pagination."""

    def __init__(self, bearer_token: str):
        if not bearer_token or not bearer_token.strip():
            raise TwitterAPIError("Twitter API bearer token is missing or empty. Please set TWITTER_API_KEY in your environment variables.")

        try:
            self.client = tweepy.Client(bearer_token=bearer_token.strip())
            # Test the connection with a minimal request
            self.client.get_me()
            _LOG.info("Twitter API authentication successful")
        except tweepy.Unauthorized:
            raise TwitterAPIError("Twitter API authentication failed: Invalid bearer token. Please check your TWITTER_API_KEY.")
        except tweepy.Forbidden:
            raise TwitterAPIError("Twitter API authentication failed: Access forbidden. Your bearer token may not have the required permissions.")
        except tweepy.TweepyException as e:
            raise TwitterAPIError(f"Twitter API authentication failed: {str(e)}")
        except Exception as e:
            raise TwitterAPIError(f"Failed to initialize Twitter API client: {str(e)}")

    def search_tweets(
        self,
        query: str,
        max_results: int = 15,  # Changed default to 15 (between 10-20 as specified)
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        lang: Optional[str] = None,
        next_token: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Search tweets with pagination and query parameters.

        Args:
            query: Search query (supports hashtags, keywords, etc.)
            max_results: Maximum results per request (10-100)
            start_time: Start time in ISO 8601 format
            end_time: End time in ISO 8601 format
            lang: Language code (e.g., 'en')
            next_token: Token for pagination
            max_retries: Maximum number of retries on rate limit errors

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
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        # Implement retry logic with exponential backoff
        sanitized_query = _URL_RE.sub("[URL]", full_query)
        for attempt in range(max_retries + 1):
            try:
                _LOG.debug(f"Twitter API search attempt {attempt + 1}/{max_retries + 1} for query: '{sanitized_query[:50]}...'")

                response = self.client.search_recent_tweets(
                    query=full_query,
                    max_results=min(max_results, 100),
                    start_time=start_dt,
                    end_time=end_dt,
                    next_token=next_token,
                    tweet_fields=["created_at", "public_metrics", "lang", "text", "author_id", "referenced_tweets"],
                    user_fields=["username"],
                    expansions=["author_id"]
                )

                tweets = []
                users = {}
                if response.data:
                    tweets = response.data
                    if response.includes and "users" in response.includes:
                        users = {user.id: user for user in response.includes["users"]}

                result = {
                    "tweets": tweets,
                    "users": users,
                    "next_token": response.meta.get("next_token") if response.meta else None
                }

                _LOG.info(f"Twitter API search successful: found {len(tweets)} tweets")
                return result

            except tweepy.TooManyRequests as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    _LOG.warning(f"Twitter API rate limit exceeded. Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    _LOG.error(f"Twitter API rate limit exceeded after {max_retries + 1} attempts")
                    raise TwitterAPIError(f"Twitter API rate limit exceeded after {max_retries + 1} attempts. Please try again later.")

            except tweepy.BadRequest as e:
                raise TwitterAPIError(f"Invalid search query: '{sanitized_query[:50]}...'. Please check your query syntax.")
            except tweepy.Unauthorized as e:
                raise TwitterAPIError("Twitter API authentication failed during search. Token may be invalid.")
            except tweepy.TweepyException as e:
                error_msg = f"Twitter API error: {str(e)}"
                _LOG.error(error_msg)
                raise TwitterAPIError(error_msg)

            except Exception as e:
                error_msg = f"Unexpected error during Twitter API search: {str(e)}"
                _LOG.error(error_msg)
                raise TwitterAPIError(error_msg)

        # This should never be reached, but just in case
        raise TwitterAPIError("Twitter API search failed after all retry attempts")

    def normalize_tweet(self, tweet: tweepy.Tweet, users: Dict[str, tweepy.User]) -> Optional[NormalizedTweet]:
        """Normalize raw tweet data to our schema."""
        # Skip retweets
        if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
            for ref in tweet.referenced_tweets:
                if ref.type == 'retweeted':
                    _LOG.debug(f"Skipping retweet: {tweet.id}")
                    return None
        
        # Skip if no text or media-only (assuming if text is empty or just URLs)
        if not hasattr(tweet, 'text') or not tweet.text or not tweet.text.strip():
            _LOG.debug(f"Skipping media-only or empty tweet: {getattr(tweet, 'id', 'unknown')}")
            return None
        
        author = users.get(getattr(tweet, 'author_id', ''))
        author_handle = author.username if author else ""
        
        # Skip if no author
        if not author_handle:
            _LOG.debug(f"Skipping tweet with missing author: {getattr(tweet, 'id', 'unknown')}")
            return None
        
        sanitized_text = sanitize_text(tweet.text)
        
        # If after sanitization, text is empty, skip
        if not sanitized_text:
            _LOG.debug(f"Skipping tweet with no content after sanitization: {getattr(tweet, 'id', 'unknown')}")
            return None
        
        # Ensure timestamp is ISO 8601 UTC
        timestamp = ""
        if hasattr(tweet, 'created_at') and tweet.created_at:
            # Ensure it's UTC
            if tweet.created_at.tzinfo is None:
                # Assume UTC if naive
                dt = tweet.created_at.replace(tzinfo=timezone.utc)
            else:
                dt = tweet.created_at.astimezone(timezone.utc)
            timestamp = dt.isoformat()
        
        # Extract public_metrics dict once
        metrics = getattr(tweet, 'public_metrics', None)
        if not isinstance(metrics, dict):
            metrics = {}
        
        return NormalizedTweet(
            text=sanitized_text,
            author_handle=author_handle,
            permalink=f"https://twitter.com/{author_handle}/status/{getattr(tweet, 'id', '')}",
            created_timestamp=timestamp,
            like_count=metrics.get("like_count", 0),
            repost_count=metrics.get("retweet_count", 0),
            reply_count=metrics.get("reply_count", 0),
            language=getattr(tweet, 'lang', '') or "",
            platform="twitter"
        )


class TwitterTool(BaseTool):
    """Fetches relevant Twitter posts based on a user query."""

    name: str = "twitter_search"
    description: str = "Search Twitter for discussions related to customer pain points. Supports hashtags, keywords, language filters, and time windows."
    settings: Any
    _wrapper: TwitterAPIWrapper = PrivateAttr(default=None)

    def __init__(self, settings: Settings) -> None:
        # Validate settings has Twitter API key
        if not hasattr(settings, 'api') or not hasattr(settings.api, 'twitter_api_key'):
            raise TwitterAPIError("Twitter API key not found in settings. Please ensure TWITTER_API_KEY is set in your environment variables.")

        try:
            wrapper = TwitterAPIWrapper(settings.api.twitter_api_key)
            _LOG.info("TwitterTool initialized successfully")
        except TwitterAPIError:
            raise  # Re-raise TwitterAPIError as-is
        except Exception as e:
            _LOG.error(f"Failed to initialize TwitterTool: {str(e)}")
            raise TwitterAPIError(f"Failed to initialize TwitterTool: {str(e)}")

        # Initialize Pydantic model with required fields
        super().__init__(settings=settings)
        self._wrapper = wrapper

    @classmethod
    def from_settings(cls, settings: Settings) -> "TwitterTool":
        """Factory method to create a tool instance from global settings."""
        return cls(settings)

    def _run(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Synchronously execute the tool and return search results."""
        start_time = time.time()

        # Log search request (masking any sensitive data)
        safe_query = query.replace('\n', ' ').replace('\r', ' ')[:100]  # Truncate and clean
        safe_filters = {k: kwargs.get(k) for k in ("max_results", "lang", "start_time", "end_time")}
        _LOG.info(f"Twitter search initiated: query='{safe_query}'..., filters={safe_filters}")

        try:
            response = self._wrapper.search_tweets(
                query=query,
                max_results=kwargs.get("max_results", 15),  # Default to 15 tweets
                start_time=kwargs.get("start_time"),
                end_time=kwargs.get("end_time"),
                lang=kwargs.get("lang")
            )

            normalized_tweets = []
            for tweet in response["tweets"]:
                normalized = self._wrapper.normalize_tweet(tweet, response["users"])
                if normalized is not None:
                    normalized_tweets.append(normalized.dict())

            execution_time = time.time() - start_time
            _LOG.info(f"Twitter search completed: {len(normalized_tweets)} tweets found in {execution_time:.2f}s")

            return normalized_tweets

        except TwitterAPIError:
            raise  # Re-raise TwitterAPIError as-is
        except Exception as e:
            # Note: Unlike RedditTool which returns empty list on errors, TwitterTool raises
            # exceptions to provide clear feedback about API issues (auth failures, rate limits, etc.)
            # This allows calling code to handle different error types appropriately
            execution_time = time.time() - start_time
            _LOG.error(f"Twitter search failed after {execution_time:.2f}s: {str(e)}")
            raise TwitterAPIError(f"Twitter search failed: {str(e)}")

    async def _arun(
        self,
        query: str,
        max_results: int = 15,  # Default to 15 tweets
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        lang: Optional[str] = None,
        *args: Any,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Asynchronously execute the tool and return search results.

        Args:
            query: Search query
            max_results: Number of results to fetch (default: 15)
            start_time: ISO 8601 start time
            end_time: ISO 8601 end time
            lang: Language code

        Returns:
            List of normalized tweet dictionaries
        """
        execution_start = time.time()

        # Log search request (masking any sensitive data)
        safe_query = query.replace('\n', ' ').replace('\r', ' ')[:100]  # Truncate and clean
        _LOG.info(f"Async Twitter search initiated: query='{safe_query}'..., max_results={max_results}")

        try:
            # For simplicity, since tweepy is sync, run in thread
            def _sync_search():
                return self._wrapper.search_tweets(
                    query=query,
                    max_results=max_results,
                    start_time=start_time,
                    end_time=end_time,
                    lang=lang,
                    next_token=None
                )
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, _sync_search)

            normalized_tweets = []
            for tweet in response["tweets"]:
                normalized = self._wrapper.normalize_tweet(tweet, response["users"])
                if normalized is not None:
                    normalized_tweets.append(normalized.dict())

            execution_time = time.time() - execution_start
            _LOG.info(f"Async Twitter search completed: {len(normalized_tweets)} tweets found in {execution_time:.2f}s")

            return normalized_tweets

        except TwitterAPIError:
            raise  # Re-raise TwitterAPIError as-is
        except Exception as e:
            execution_time = time.time() - execution_start
            _LOG.error(f"Async Twitter search failed after {execution_time:.2f}s: {str(e)}")
            raise TwitterAPIError(f"Async Twitter search failed: {str(e)}")
