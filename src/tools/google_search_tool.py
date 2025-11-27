from __future__ import annotations

from typing import Any, Dict, List
import logging
from pydantic import PrivateAttr

from langchain.tools import BaseTool

from config.settings import Settings


logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency guard
    from googleapiclient.errors import HttpError
except Exception:  # pragma: no cover - library missing at import time
    class HttpError(Exception):
        """Fallback error type when googleapiclient is not installed."""


class GoogleSearchTool(BaseTool):
    """Fetches relevant Google Search results based on a user query.

    Implementation notes / best-practices:
    - The Google API client library is optional; we guard the import and
      provide clear error messages if it's not available.
    - The API service is created once during initialization and reused for
      subsequent calls to reduce latency.
    - Keys returned by the Google API are normalized to snake_case for
      consistency with Python conventions.
    """

    name: str = "google_search"
    description: str = "Search Google for discussions related to customer pain points."

    settings: Any = None
    _service: Any = PrivateAttr(default=None)

    def __init__(self, settings: Settings) -> None:
        # Initialize BaseTool fields
        super().__init__(settings=settings)
        api_key = settings.api.google_search_api_key
        cse_id = settings.api.google_search_engine_id

        if not api_key or not cse_id:
            # Align with existing tools' behavior: log a warning and allow
            # instantiation for testing/development; fail when _run() is used.
            logger.warning(
                "GoogleSearchTool instantiated without API credentials; calls to _run() will fail until credentials are set."
            )
            self._service = None
            return

        try:
            from googleapiclient.discovery import build
        except ImportError:  # pragma: no cover - dependency/runtime guard
            logger.error(
                "google-api-python-client is not installed; install with `pip install google-api-python-client`"
            )
            self._service = None
            return

        # Create the service once and reuse it for subsequent calls
        self._service = build("customsearch", "v1", developerKey=api_key)

    @classmethod
    def from_settings(cls, settings: Settings) -> "GoogleSearchTool":
        """Factory method to create a tool instance from global settings."""

        return cls(settings)

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Return a consistent schema for Google Custom Search results."""

        return {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "display_link": item.get("displayLink", ""),
            "cache_id": item.get("cacheId", ""),
        }

    def _run(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Synchronously execute the tool and return search results.

        Raises RuntimeError with context on missing credentials or API failures.
        """

        if not self._service:
            raise RuntimeError(
                "GoogleSearchTool is not configured with an API client. Ensure GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID are set and google-api-python-client is installed."
            )

        requested_num = kwargs.get("num", 10)
        try:
            num = int(requested_num)
        except (TypeError, ValueError):
            num = 10

        if num < 1:
            num = 1

        # Google Custom Search API caps the `num` parameter at 10 results.
        num = min(num, 10)

        params = {"q": query, "cx": self.settings.api.google_search_engine_id, "num": num}

        try:
            res = self._service.cse().list(**params).execute()
        except HttpError as exc:
            logger.exception("Google Custom Search API returned an HTTP error")
            raise RuntimeError(f"Google Custom Search request failed: {exc}") from exc
        except OSError as exc:
            logger.exception("Google Custom Search API request encountered a network error")
            raise RuntimeError(f"Google Custom Search request failed: {exc}") from exc

        items = res.get("items", [])
        return [self._normalize_item(i) for i in items]

    async def _arun(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Asynchronously execute the tool and return search results.

        This currently delegates to the synchronous implementation.
        """

        return self._run(query, *args, **kwargs)
