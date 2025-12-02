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

    query: str = Field(..., description="Search query to run against Reddit.")
    subreddits: List[str] = Field(
        default_factory=lambda: ["all"],
        description="One or more subreddit names to search (defaults to 'all').",
    )
    limit: int = Field(
        15,
        ge=1,
        le=20,
        description="Total number of posts to return across subreddits (capped at 20).",
    )
    per_subreddit: int = Field(
        10,
        ge=1,
        le=25,
        description="Posts to fetch per subreddit before merging and deduping.",
    )
    time_filter: Optional[Literal["hour", "day", "week", "month", "year", "all"]] = Field(
        None,
        description="Optional Reddit time filter window.",
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
    description: str = "Search Reddit for discussions related to customer pain points."
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

        # Initialize PRAW Reddit client
        self._client = praw.Reddit(
            client_id=client_id or "",
            client_secret=client_secret or "",
            user_agent=user_agent,
            check_for_async=False,
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

    def _fetch_subreddit(self, subreddit_name: str, query: str, limit: int, time_filter: Optional[str], retries: int = 2) -> List[Dict[str, Any]]:
        """Fetch search results for a single subreddit with simple retry/backoff."""

        attempt = 0
        backoff = 0.5
        while attempt <= retries:
            try:
                subreddit = self._client.subreddit(subreddit_name)
                # Measure fetch duration to help detect slow or rate-limited calls.
                t0 = time.time()
                submissions = subreddit.search(query, limit=limit, sort="relevance", time_filter=time_filter)
                t1 = time.time()
                # Hand off PRAW objects to the parsing helper which fulfils the
                # sanitisation acceptance criteria for story 1.2.3.
                results = [normalize_submission(s) for s in submissions]
                _LOG.debug(
                    "Fetched %d items from r/%s in %.2f seconds",
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
                _LOG.warning("Error fetching r/%s (attempt %d/%d): %s", subreddit_name, attempt + 1, retries + 1, exc)
                attempt += 1
                # If we've exhausted retries, avoid sleeping unnecessarily
                # before exiting the loop.
                if attempt > retries:
                    break

                time.sleep(backoff)
                backoff *= 2

        _LOG.error("Failed to fetch subreddit %s after %d attempts", subreddit_name, retries + 1)
        return []

    def _merge_and_sort(self, lists: Iterable[List[Dict[str, Any]]], total_limit: int) -> List[Dict[str, Any]]:
        """Merge results from multiple subreddits, dedupe by `id`, and sort by relevance."""

        seen = set()
        merged: List[Dict[str, Any]] = []
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

                seen.add(item_id)
                merged.append(item)

        # Relevance: upvotes + comments (simple heuristic)
        merged.sort(key=lambda x: (x.get("upvotes", 0) + x.get("comments", 0)), reverse=True)
        return merged[:total_limit]

    def _run(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        limit: int = 15,
        per_subreddit: int = 10,
        time_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronously execute the tool and return normalized search results."""

        subreddits = subreddits or ["all"]
        total_limit = max(1, min(int(limit), 20))
        per_subreddit = max(1, min(int(per_subreddit), 25))
        # PRAW rejects None; default to a conservative window if not provided.
        time_filter = time_filter or "week"

        start = time.time()
        results_by_sub: List[List[Dict[str, Any]]] = []

        try:
            with ThreadPoolExecutor(max_workers=min(8, len(subreddits))) as exc:
                futures = {exc.submit(self._fetch_subreddit, s, query, per_subreddit, time_filter): s for s in subreddits}
                for fut in as_completed(futures):
                    try:
                        results_by_sub.append(fut.result())
                    except Exception as exc:  # pragma: no cover - defensive
                        _LOG.exception("Unhandled exception while fetching subreddit: %s", exc)

            merged = self._merge_and_sort(results_by_sub, total_limit)
            duration = time.time() - start
            _LOG.info("RedditTool: returning %d posts in %.2f seconds", len(merged), duration)
            return merged
        except Exception as exc:
            _LOG.exception("RedditTool encountered an unexpected error: %s", exc)
            return []

    async def _arun(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Async wrapper for LangChain compatibility; runs the sync implementation."""

        return self._run(query, *args, **kwargs)

