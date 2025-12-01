"""Google Search retrieval tool for the pain point agent."""

from __future__ import annotations

from typing import Any, Dict, List

from langchain.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from config.settings import Settings


class GoogleSearchToolInput(BaseModel):
    """Input schema for GoogleSearchTool."""

    query: str = Field(..., description="Search query for Google Custom Search.")

    model_config = ConfigDict(extra="forbid")


class GoogleSearchTool(BaseTool):
    """Fetches relevant Google Search results based on a user query."""

    name: str = "google_search"
    description: str = "Search Google for discussions related to customer pain points."
    args_schema: type[BaseModel] = GoogleSearchToolInput

    settings: Any = None

    def __init__(self, settings: Settings) -> None:
        # Initialize pydantic/model fields via super().__init__ so assignment
        # respects BaseTool's model semantics.
        super().__init__(settings=settings)
        # Initialize Google Search client here when implementing

    @classmethod
    def from_settings(cls, settings: Settings) -> "GoogleSearchTool":
        """Factory method to create a tool instance from global settings."""

        return cls(settings)

    def _run(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Synchronously execute the tool and return search results."""

        raise NotImplementedError("GoogleSearchTool._run must be implemented")

    async def _arun(self, query: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Asynchronously execute the tool and return search results."""

        raise NotImplementedError("GoogleSearchTool._arun must be implemented")
