"""Reddit data retrieval tool for the pain point agent.

This module implements a light-weight wrapper around PRAW that produces a
normalized list of post dictionaries suitable for downstream extraction.

Acceptance highlights implemented:
- Search multiple subreddits in parallel using ThreadPoolExecutor.
- Return configurable number of posts (default target between 10-20).
- Each post includes: title, body, url, author, subreddit, timestamp, score, comments.
- Graceful error handling with logging and empty-list fallback.
"""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Iterable, List, Literal, Optional

import praw
from langchain.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator

from config.settings import Settings
from src.tools.reddit_parser import normalize_submission


class RedditToolInput(BaseModel):
    """Input schema for RedditTool."""

    query: str = Field(
        ..., 
        description="The exact search terms from the user's question. Pass the user's query directly without modification."
    )
    subreddits: List[str] = Field(
        default_factory=lambda: ["smallbusiness", "Entrepreneur", "startups", "CustomerService", "BusinessTips", "SaaS"],
        description="One or more subreddit names to search. Use specific, topic-relevant subreddits to get better quality results.",
    )
    limit: int = Field(
        10,
        ge=1,
        le=20,
        description="Total number of posts to return across subreddits (capped at 20).",
    )
    per_subreddit: int = Field(
        5,
        ge=1,
        le=25,
        description="Posts to fetch per subreddit before merging and deduping.",
    )
    time_filter: Optional[Literal["hour", "day", "week", "month", "year", "all"]] = Field(
        "month",
        description="Reddit time filter window. Defaults to 'month' for relevant recent content.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("subreddits", mode="before")
    @classmethod
    def _coerce_subreddits(cls, value: Any) -> List[str]:
        if value is None:
            return ["all"]
        if isinstance(value, str):
            return [value]
        return value

_LOG = logging.getLogger(__name__)


class RedditTool(BaseTool):
    """Fetches relevant Reddit posts based on a user query.

    Public API (used by LangChain tooling):
    - `_run(query, subreddits=None, limit=15, time_filter=None)` returns a list
      of normalized post dicts.
    """

    name: str = "reddit_search"
    description: str = (
        "Search Reddit for posts matching a specific query. "
        "The 'query' parameter MUST be the user's actual search terms - pass them exactly as provided. "
        "Returns posts with title, body, author, subreddit, and engagement metrics."
    )
    args_schema: type[BaseModel] = RedditToolInput

    settings: Any = None
    _client: Any = PrivateAttr(default=None)

    def __init__(self, settings: Settings) -> None:
        # Initialize pydantic/model fields via super().__init__ so assignment
        # respects BaseTool's model semantics.
        super().__init__(settings=settings)
        client_id = getattr(settings.api, "reddit_client_id", None)
        client_secret = getattr(settings.api, "reddit_client_secret", None)
        user_agent = os.getenv("REDDIT_USER_AGENT", "customer-pain-point-agent/0.1")

        if not client_id or not client_secret:
            _LOG.warning("Reddit credentials not provided in settings; client will still be created but may fail on use.")

        # Initialize PRAW Reddit client with timeout and rate limit settings
        # to prevent connection exhaustion during rapid agent calls
        self._client = praw.Reddit(
            client_id=client_id or "",
            client_secret=client_secret or "",
            user_agent=user_agent,
            check_for_async=False,
            timeout=30,  # Request timeout in seconds
            ratelimit_seconds=300,  # Wait up to 5 min if rate limited
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "RedditTool":
        """Factory method to create a tool instance from global settings."""

        return cls(settings)

    def _normalize_submission(self, submission: Any) -> Dict[str, Any]:
        """Extract required fields from a PRAW Submission-like object."""
        # Normalize subreddit to a string using helper.
        subreddit_str = self._extract_subreddit(submission)
        author_str = self._extract_author(submission)
        score = int(getattr(submission, "score", 0) or 0)
        body = getattr(submission, "selftext", "")

        return {
            "id": getattr(submission, "id", ""),
            "title": getattr(submission, "title", ""),
            "body": body,
            "author": author_str,
            "score": score,
            "comments": int(getattr(submission, "num_comments", 0) or 0),
            "url": getattr(submission, "url", ""),
            "subreddit": subreddit_str,
            "timestamp": float(getattr(submission, "created_utc", 0) or 0),
        }

    def _extract_subreddit(self, submission: Any) -> str:
        """Return a normalized subreddit string for a submission.

        Handles cases where `submission.subreddit` may be a string, a PRAW
        Subreddit-like object, or missing. Preference order:
        1. If `subreddit` is a string, return it.
        2. If `subreddit_name_prefixed` is present, return it.
        3. Otherwise, attempt `str(subreddit)` and fall back to empty string.
        """
        sub_attr = getattr(submission, "subreddit", None)

        if isinstance(sub_attr, str):
            return sub_attr

        # Try explicit prefixed name first (common on PRAW submissions)
        pref = getattr(submission, "subreddit_name_prefixed", None)
        if pref:
            return pref

        # Fall back to stringifying the object if present
        if sub_attr is not None:
            try:
                return str(sub_attr)
            except Exception:
                _LOG.debug("Failed to stringify subreddit object: %r", sub_attr)

        return ""

    def _extract_author(self, submission: Any) -> str:
        """Return a normalized author string if present on a submission."""

        author_attr = getattr(submission, "author", None)
        if isinstance(author_attr, str):
            return author_attr

        if author_attr is None:
            return ""

        # PRAW author objects implement `.name`; fall back to str() if missing.
        name_attr = getattr(author_attr, "name", None)
        if name_attr:
            return str(name_attr)

        try:
            return str(author_attr)
        except Exception:
            _LOG.debug("Failed to stringify author object: %r", author_attr)
            return ""

    def _fetch_subreddit(self, subreddit_name: str, query: str, limit: int, time_filter: Optional[str], retries: int = 4) -> List[Dict[str, Any]]:
        """Fetch search results for a single subreddit with retry/backoff.
        
        Increased retries from 2 to 4 to handle rate-limited subreddits better.
        """

        attempt = 0
        # Start with a longer backoff to respect Reddit rate limits
        # This helps avoid connection exhaustion during rapid agent calls
        backoff = 2.0
        while attempt <= retries:
            # Small delay before each attempt to avoid overwhelming Reddit
            if attempt > 0:
                _LOG.info("Retry attempt %d/%d for r/%s after %.1fs backoff", attempt, retries, subreddit_name, backoff)
            try:
                subreddit = self._client.subreddit(subreddit_name)
                # Measure fetch duration to help detect slow or rate-limited calls.
                t0 = time.time()
                submissions = subreddit.search(query, limit=limit, sort="relevance", time_filter=time_filter)
                t1 = time.time()
                # Hand off PRAW objects to the parsing helper which fulfils the
                # sanitisation acceptance criteria for story 1.2.3.
                results = [normalize_submission(s) for s in submissions]
                _LOG.info(
                    "Successfully fetched %d items from r/%s in %.2f seconds",
                    len(results), subreddit_name, t1 - t0,
                )

                # If the reddit client exposes rate limit info, log it for diagnostics.
                try:
                    rl = getattr(self._client, "auth", None)
                    if rl is not None:
                        _LOG.debug("Reddit auth info: %s", getattr(rl, "limits", "<no-limits>"))
                except Exception:
                    # Non-fatal: presence of rate-limit attributes varies by PRAW version
                    pass

                return results
            except Exception as exc:
                exc_str = str(exc).lower()
                # Check if this is a rate limit or connection error that might benefit from retry
                is_retryable = any(keyword in exc_str for keyword in ["rate", "limit", "429", "timeout", "connection"])
                _LOG.warning(
                    "Error fetching r/%s (attempt %d/%d, retryable=%s): %s", 
                    subreddit_name, attempt + 1, retries + 1, is_retryable, exc
                )
                attempt += 1
                # If we've exhausted retries, avoid sleeping unnecessarily
                # before exiting the loop.
                if attempt > retries:
                    break

                time.sleep(backoff)
                backoff *= 1.5  # Multiplicative backoff: 2s -> 3s -> 4.5s -> 6.75s -> 10.1s

        _LOG.error("Failed to fetch subreddit r/%s after %d attempts - posts from this subreddit will be skipped", subreddit_name, retries + 1)
        return []

    def _check_relevance(self, post: Dict[str, Any], query: str) -> bool:
        """Check if a post is relevant to the search query using weighted scoring.
        
        Uses a weighted scoring system:
        - Generic terms (api, error, bug, etc.) get weight 1
        - Specific/primary terms get weight 3
        - Posts must score >= 3 (at least one primary term) to pass
        
        This prevents generic API posts from matching queries about specific APIs.
        """
        if not query or len(query) <= 2:
            # For very short or empty queries, accept all posts
            return True
        
        # Generic terms that are common across many topics
        GENERIC_TERMS = {
            "api", "apis", "issue", "issues", "problem", "problems",
            "error", "errors", "bug", "bugs", "help", "question",
            "code", "coding", "dev", "developer", "developers",
            "calling", "call", "use", "using", "used",
            "pain", "point", "points", "report", "reports",
            "when", "how", "what", "why", "the", "and", "for",
        }
        
        # Extract query terms (simple tokenization)
        query_lower = query.lower()
        query_terms = [term for term in query_lower.split() if len(term) > 2]
        
        # If no meaningful terms, accept the post
        if not query_terms:
            return True
        
        # Separate primary (specific) and generic terms
        primary_terms = [t for t in query_terms if t not in GENERIC_TERMS]
        generic_terms = [t for t in query_terms if t in GENERIC_TERMS]
        
        # Get post content
        title = (post.get("title") or "").lower()
        text = (post.get("text") or "").lower()
        combined_text = f"{title} {text}"
        
        # Calculate weighted score
        score = 0
        matched_primary = []
        matched_generic = []
        
        for term in primary_terms:
            if term in combined_text:
                score += 3  # Primary terms are worth 3 points
                matched_primary.append(term)
        
        for term in generic_terms:
            if term in combined_text:
                score += 1  # Generic terms are worth 1 point
                matched_generic.append(term)
        
        # Require at least one primary term match (score >= 3)
        # OR if there are no primary terms in query, require all generic terms
        if primary_terms:
            is_relevant = score >= 3  # At least one primary term matched
        else:
            # No primary terms in query - fall back to old behavior
            is_relevant = score > 0
        
        if not is_relevant:
            _LOG.debug(
                "Relevance check failed for '%s': score=%d, primary=%s, generic=%s",
                (post.get("title") or "")[:40], score, matched_primary, matched_generic
            )
        
        return is_relevant

    def _merge_and_sort(self, lists: Iterable[List[Dict[str, Any]]], total_limit: int, query: str = "") -> List[Dict[str, Any]]:
        """Merge results from multiple subreddits, dedupe by `id`, filter by relevance, and sort.
        
        Args:
            lists: Lists of posts from different subreddits
            total_limit: Maximum number of posts to return
            query: Search query used to filter for relevance
        """

        seen = set()
        merged: List[Dict[str, Any]] = []
        filtered_count = 0
        
        for lst in lists:
            for item in lst:
                item_id = item.get("id")
                # Explicitly skip items that don't have a valid id (None or empty
                # string). If we allow falsy ids through, multiple items without
                # ids can be added and will not be deduplicated.
                if not item_id:
                    _LOG.debug("Skipping item without id during merge: %s", item)
                    continue

                if item_id in seen:
                    continue

                # Check relevance to query
                if query and not self._check_relevance(item, query):
                    filtered_count += 1
                    _LOG.debug("Filtered out irrelevant post: %s", item.get("title", "")[:60])
                    continue

                seen.add(item_id)
                merged.append(item)

        if filtered_count > 0:
            _LOG.info("Filtered out %d posts that were not relevant to query", filtered_count)

        # Relevance: upvotes + comments (simple heuristic)
        merged.sort(key=lambda x: (x.get("upvotes", 0) + x.get("comments", 0)), reverse=True)
        return merged[:total_limit]

    def _run(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        limit: int = 10,
        per_subreddit: int = 5,
        time_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronously execute the tool and return normalized search results."""

        # Use specific subreddits by default to avoid rate limits on r/all
        # Expanded list provides more diversity and reduces over-reliance on same subreddits
        subreddits = subreddits or ["smallbusiness", "Entrepreneur", "startups", "CustomerService", "BusinessTips", "SaaS"]
        total_limit = max(1, min(int(limit), 20))
        per_subreddit = max(1, min(int(per_subreddit), 25))
        # PRAW rejects None; default to a conservative window if not provided.
        time_filter = time_filter or "week"

        start = time.time()
        results_by_sub: List[List[Dict[str, Any]]] = []

        try:
            # Limit concurrent requests to avoid overwhelming Reddit's API
            # and causing connection exhaustion / rate limiting
            max_workers = min(2, len(subreddits))
            with ThreadPoolExecutor(max_workers=max_workers) as exc:
                futures = {exc.submit(self._fetch_subreddit, s, query, per_subreddit, time_filter): s for s in subreddits}
                for fut in as_completed(futures):
                    try:
                        results_by_sub.append(fut.result())
                    except Exception as exc:  # pragma: no cover - defensive
                        _LOG.exception("Unhandled exception while fetching subreddit: %s", exc)

            merged = self._merge_and_sort(results_by_sub, total_limit, query)
            duration = time.time() - start
            _LOG.info("RedditTool: returning %d posts in %.2f seconds", len(merged), duration)
            
            # Log post titles for debugging/verification
            if merged:
                _LOG.info("RedditTool posts returned:")
                for i, post in enumerate(merged[:5], 1):  # Log first 5 posts
                    title = post.get("title", "")[:80]
                    subreddit = post.get("subreddit", "unknown")
                    _LOG.info("  %d. [r/%s] %s", i, subreddit, title)
                if len(merged) > 5:
                    _LOG.info("  ... and %d more posts", len(merged) - 5)
            
            return merged
        except Exception as exc:
            _LOG.exception("RedditTool encountered an unexpected error: %s", exc)
            return []

    async def _arun(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Async wrapper for LangChain compatibility; runs the sync implementation."""

        return self._run(query, *args, **kwargs)

