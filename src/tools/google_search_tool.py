"""Google Search retrieval tool for the pain point agent."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.tools import BaseTool
from pydantic import PrivateAttr

from config.settings import Settings
from src.tools.google_parser import normalize_google_result

_LOG = logging.getLogger(__name__)


class GoogleSearchTool(BaseTool):
    """Fetches relevant Google Search results based on a user query."""

    name: str = "google_search"
    description: str = "Search Google for discussions related to customer pain points."

    settings: Any = None
    _client: Any = PrivateAttr(default=None)

    def __init__(self, settings: Settings) -> None:
        # Initialize pydantic/model fields via super().__init__ so assignment
        # respects BaseTool's model semantics.
        super().__init__(settings=settings)
        
        api_key = getattr(settings.api, "google_search_api_key", "")
        engine_id = getattr(settings.api, "google_search_engine_id", "")
        
        if not api_key or not engine_id:
            _LOG.warning("Google Search credentials not provided in settings; tool will still be created but may fail on use.")
        
        # Initialize Google Custom Search client
        self._client = build("customsearch", "v1", developerKey=api_key)

    @classmethod
    def from_settings(cls, settings: Settings) -> "GoogleSearchTool":
        """Factory method to create a tool instance from global settings."""

        return cls(settings)

    def _normalize_result(self, item: Dict[str, Any], position: int) -> Optional[Dict[str, Any]]:
        """Normalize a Google Custom Search result using the dedicated parser."""
        return normalize_google_result(item, position)

    def _run(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Synchronously execute the tool and return search results.

        Expected kwargs:
        - num: int number of results to return (default 10, max 10)
        - lang: str language restriction (default None)
        - site: str site restriction (default None)
        """
        num_results = min(int(kwargs.get("num", 10)), 10)  # API max is 10
        lang = kwargs.get("lang")
        site = kwargs.get("site")
        
        start_time = time.time()
        
        # Build search parameters
        search_params = {
            "q": query,
            "cx": getattr(self.settings.api, "google_search_engine_id", ""),
            "num": num_results,
        }
        
        if lang:
            search_params["lr"] = f"lang_{lang}"
        if site:
            search_params["siteSearch"] = site
        
        max_retries = 3
        backoff = 1.0
        
        for attempt in range(max_retries):
            try:
                _LOG.debug("Google Search attempt %d/%d for query: %s", attempt + 1, max_retries, query)
                
                response = self._client.cse().list(**search_params).execute()
                
                items = response.get("items", [])
                normalized_results = [
                    self._normalize_result(item, i + 1) 
                    for i, item in enumerate(items)
                ]
                # Filter out None results (non-web results that were skipped)
                normalized_results = [r for r in normalized_results if r is not None]
                
                duration = time.time() - start_time
                _LOG.info(
                    "GoogleSearchTool: returning %d results in %.2f seconds for query: %s",
                    len(normalized_results), duration, query
                )
                
                return normalized_results
                
            except HttpError as exc:
                error_details = exc.error_details if hasattr(exc, 'error_details') else []
                is_quota_error = any(
                    detail.get('reason') == 'quotaExceeded' or 'quota' in detail.get('message', '').lower()
                    for detail in error_details
                )
                
                if is_quota_error and attempt < max_retries - 1:
                    _LOG.warning(
                        "Google Search quota exceeded (attempt %d/%d), retrying in %.1f seconds: %s",
                        attempt + 1, max_retries, backoff, exc
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    _LOG.error("Google Search API error: %s", exc)
                    raise
                    
            except Exception as exc:
                _LOG.error("Unexpected error in Google Search: %s", exc)
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise
        
        # This should not be reached, but just in case
        _LOG.error("Google Search failed after %d attempts", max_retries)
        return []

    async def _arun(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Asynchronously execute the tool and return search results."""
        # Run the blocking call in a thread pool to avoid blocking the event loop
        import asyncio
        return await asyncio.to_thread(self._run, query, *args, **kwargs)
