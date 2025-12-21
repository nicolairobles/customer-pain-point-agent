"""Application configuration and environment variable management."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class APISettings:
    """Holds API credential configuration for external services."""

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    google_search_api_key: str = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    google_search_engine_id: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")


@dataclass(frozen=True)
class AgentSettings:
    """General configuration values for the agent runtime."""

    max_results_per_source: int = int(os.getenv("MAX_RESULTS_PER_SOURCE", "10"))
    source_timeout_seconds: int = int(os.getenv("SOURCE_TIMEOUT_SECONDS", "30"))
    total_timeout_seconds: int = int(os.getenv("TOTAL_TIMEOUT_SECONDS", "120"))
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "15"))
    verbose: bool = os.getenv("AGENT_VERBOSE", "false").lower() == "true"


@dataclass(frozen=True)
class AggregationSettings:
    """Configuration for cross-source aggregation and scoring."""

    recency_weight: float = float(os.getenv("AGGREGATION_RECENCY_WEIGHT", "0.55"))
    engagement_weight: float = float(os.getenv("AGGREGATION_ENGAGEMENT_WEIGHT", "0.45"))
    max_item_age_days: int = int(os.getenv("AGGREGATION_MAX_ITEM_AGE_DAYS", "365"))
    near_duplicate_threshold: float = float(os.getenv("AGGREGATION_NEAR_DUPLICATE_THRESHOLD", "0.82"))
    comment_weight: float = float(os.getenv("AGGREGATION_COMMENT_WEIGHT", "0.5"))
    reddit_source_weight: float = float(os.getenv("AGGREGATION_REDDIT_WEIGHT", "1.0"))
    google_source_weight: float = float(os.getenv("AGGREGATION_GOOGLE_WEIGHT", "0.9"))
    default_source_weight: float = float(os.getenv("AGGREGATION_DEFAULT_WEIGHT", "0.75"))
    extra_source_weights: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize aggregation weights loaded from the environment."""

        # Ensure weights are non-negative.
        if self.recency_weight < 0 or self.engagement_weight < 0:
            raise ValueError(
                "Aggregation weights must be non-negative: "
                f"recency_weight={self.recency_weight}, engagement_weight={self.engagement_weight}"
            )

        total = self.recency_weight + self.engagement_weight

        # Prevent a zero or negative total, which would break normalization and scoring semantics.
        if total <= 0:
            raise ValueError(
                "Sum of aggregation weights must be positive: "
                f"recency_weight={self.recency_weight}, engagement_weight={self.engagement_weight}"
            )

        # If the weights do not sum to 1.0, normalize them so they behave as proper weights.
        if total != 1.0:
            normalized_recency = self.recency_weight / total
            normalized_engagement = self.engagement_weight / total
            object.__setattr__(self, "recency_weight", normalized_recency)
            object.__setattr__(self, "engagement_weight", normalized_engagement)


@dataclass(frozen=True)
class BudgetSettings:
    """Tracks cost constraints for API usage."""

    openai_budget_usd: float = float(os.getenv("OPENAI_BUDGET_USD", "15"))
    total_budget_usd: float = float(os.getenv("TOTAL_BUDGET_USD", "20"))


@dataclass(frozen=True)
class LLMSettings:
    """Configuration for Large Language Model invocation."""

    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    max_output_tokens: int = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "512"))
    request_timeout_seconds: float = float(os.getenv("OPENAI_REQUEST_TIMEOUT_SECONDS", "30"))
    max_retry_attempts: int = int(os.getenv("OPENAI_MAX_RETRY_ATTEMPTS", "3"))
    retry_backoff_seconds: float = float(os.getenv("OPENAI_RETRY_BACKOFF_SECONDS", "1"))


@dataclass(frozen=True)
class ToolSettings:
    """Feature flags for enabling/disabling individual tools."""

    reddit_enabled: bool = os.getenv("TOOL_REDDIT_ENABLED", "true").lower() == "true"
    google_search_enabled: bool = os.getenv("TOOL_GOOGLE_SEARCH_ENABLED", "true").lower() == "true"


@dataclass(frozen=True)
class Settings:
    """Aggregated application settings exposed to the rest of the codebase."""

    api: APISettings = APISettings()
    agent: AgentSettings = AgentSettings()
    aggregation: AggregationSettings = AggregationSettings()
    budget: BudgetSettings = BudgetSettings()
    llm: LLMSettings = LLMSettings()
    tools: ToolSettings = ToolSettings()


settings = Settings()


def to_dict() -> Dict[str, Any]:
    """Return a dictionary representation of the current settings."""

    return {
        "api": settings.api.__dict__,
        "agent": settings.agent.__dict__,
        "aggregation": settings.aggregation.__dict__,
        "budget": settings.budget.__dict__,
        "llm": settings.llm.__dict__,
    }
