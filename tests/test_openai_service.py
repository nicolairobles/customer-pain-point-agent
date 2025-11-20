"""Unit tests for the OpenAI LLM integration service."""

from __future__ import annotations

import asyncio
from typing import Any, List

import pytest
from openai import OpenAIError

from config.settings import (
    APISettings,
    AgentSettings,
    BudgetSettings,
    LLMSettings,
    Settings,
)
from src.services.openai_llm import LLMResult, LLMUsage, OpenAIService, OpenAIServiceError


class DummyUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


class DummyResponse:
    def __init__(self, text: str, usage: DummyUsage | None = None, response_id: str = "resp_1") -> None:
        self.output_text = text
        self.usage = usage
        self.id = response_id


class DummyClient:
    def __init__(self, responses: List[Any]) -> None:
        self._responses = responses
        self.calls: int = 0

    def responses_create(self, **_: Any) -> Any:
        self.calls += 1
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    async def responses_create_async(self, **_: Any) -> Any:
        return self.responses_create()


def _make_settings(**overrides: Any) -> Settings:
    llm_settings = LLMSettings(**overrides)
    return Settings(api=APISettings(), agent=AgentSettings(), budget=BudgetSettings(), llm=llm_settings)


def test_generate_success_returns_expected_payload() -> None:
    settings = _make_settings(max_retry_attempts=2, retry_backoff_seconds=0)
    dummy_usage = DummyUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    dummy_client = DummyClient([DummyResponse("Hello world", usage=dummy_usage)])

    service = OpenAIService(
        settings=settings,
        client=_wrap_sync_client(dummy_client),
        async_client=_wrap_async_client(dummy_client),
    )

    result = service.generate("Say hi")

    assert isinstance(result, LLMResult)
    assert result.text == "Hello world"
    assert result.usage == LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, cost_usd=None)
    assert result.model == settings.llm.model
    assert dummy_client.calls == 1


def test_generate_retries_then_succeeds() -> None:
    class RetryableError(OpenAIError):
        status_code = 429

    success_response = DummyResponse("Recovered")
    dummy_client = DummyClient([RetryableError("rate limited"), success_response])
    settings = _make_settings(max_retry_attempts=3, retry_backoff_seconds=0)

    service = OpenAIService(
        settings=settings,
        client=_wrap_sync_client(dummy_client),
        async_client=_wrap_async_client(dummy_client),
    )

    result = service.generate("Test retry")

    assert result.text == "Recovered"
    assert dummy_client.calls == 2


def test_generate_raises_after_exhausting_retries() -> None:
    class FatalError(OpenAIError):
        status_code = 400

    dummy_client = DummyClient([FatalError("bad request")])
    settings = _make_settings(max_retry_attempts=1, retry_backoff_seconds=0)
    service = OpenAIService(
        settings=settings,
        client=_wrap_sync_client(dummy_client),
        async_client=_wrap_async_client(dummy_client),
    )

    with pytest.raises(OpenAIServiceError):
        service.generate("bad")


def test_agenerate_invokes_async_client() -> None:
    dummy_usage = DummyUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15)
    dummy_client = DummyClient([DummyResponse("async success", usage=dummy_usage)])
    settings = _make_settings(max_retry_attempts=2, retry_backoff_seconds=0)

    service = OpenAIService(
        settings=settings,
        client=_wrap_sync_client(dummy_client),
        async_client=_wrap_async_client(dummy_client),
    )

    result = asyncio.run(service.agenerate("async call"))

    assert result.text == "async success"
    assert dummy_client.calls == 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncWrapper:
    def __init__(self, dummy: DummyClient) -> None:
        self.responses = _SyncResponses(dummy)


class _SyncResponses:
    def __init__(self, dummy: DummyClient) -> None:
        self._dummy = dummy

    def create(self, **kwargs: Any) -> Any:
        return self._dummy.responses_create(**kwargs)


class _AsyncWrapper:
    def __init__(self, dummy: DummyClient) -> None:
        self.responses = _AsyncResponses(dummy)


class _AsyncResponses:
    def __init__(self, dummy: DummyClient) -> None:
        self._dummy = dummy

    async def create(self, **kwargs: Any) -> Any:
        return await self._dummy.responses_create_async(**kwargs)


def _wrap_sync_client(dummy: DummyClient) -> Any:
    return _SyncWrapper(dummy)


def _wrap_async_client(dummy: DummyClient) -> Any:
    return _AsyncWrapper(dummy)

