"""Google Search retrieval tool for the pain point agent."""

from __future__ import annotations

from typing import Any, Dict, List

from langchain.tools import BaseTool

from config.settings import Settings


class GoogleSearchTool(BaseTool):
    """Fetches relevant Google Search results based on a user query.

    This implements a thin wrapper around the Google Custom Search JSON API
    using `googleapiclient`. Results are normalized to a list of dictionaries
    with common keys so downstream code can consume them consistently.
    """

    name: str = "google_search"
    description: str = "Search Google for discussions related to customer pain points."

    settings: Any = None
    _api_key: str | None = None
    _cse_id: str | None = None

    def __init__(self, settings: Settings) -> None:
        # Initialize BaseTool fields
        super().__init__(settings=settings)
        self.settings = settings
        self._api_key = settings.api.google_search_api_key or None
        self._cse_id = settings.api.google_search_engine_id or None

        if not self._api_key or not self._cse_id:
            raise RuntimeError("GoogleSearchTool requires GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID to be set in settings.api")

    @classmethod
    def from_settings(cls, settings: Settings) -> "GoogleSearchTool":
        """Factory method to create a tool instance from global settings."""

        return cls(settings)

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
            "displayLink": item.get("displayLink"),
            "cacheId": item.get("cacheId"),
        }

    def _run(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Synchronously execute the tool and return search results.

        This method uses `googleapiclient.discovery.build` to call the
        Custom Search JSON API and returns a list of normalized result dicts.
        """

        try:
            from googleapiclient.discovery import build
        except Exception as e:  # pragma: no cover - dependency/runtime guard
            raise RuntimeError("google-api-python-client is required to use GoogleSearchTool") from e

        service = build("customsearch", "v1", developerKey=self._api_key)
        params = {"q": query, "cx": self._cse_id, "num": kwargs.get("num", 10)}
        res = service.cse().list(**params).execute()
        items = res.get("items", [])
        return [self._normalize_item(i) for i in items]

    async def _arun(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Asynchronously execute the tool and return search results.

        For now this calls the synchronous implementation and is provided for
        API compatibility with langchain tooling.
        """

        # Simply delegate to the sync implementation for now
        return self._run(query, *args, **kwargs)
