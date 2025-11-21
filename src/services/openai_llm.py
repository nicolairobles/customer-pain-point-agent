"""Reusable OpenAI LLM integration with retry logic and usage reporting."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from openai import AsyncOpenAI, OpenAI, OpenAIError

from config.settings import Settings

LOGGER = logging.getLogger(__name__)


class OpenAIServiceError(RuntimeError):
    """Raised when the OpenAI service encounters an unrecoverable error."""


@dataclass(frozen=True)
class LLMUsage:
    """Token usage and optional cost information for a model invocation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: Optional[float] = None


@dataclass(frozen=True)
class LLMResult:
    """Result payload returned by the OpenAI service wrapper."""

    text: str
    usage: LLMUsage
    model: str
    response_id: Optional[str]
    latency_seconds: float
    raw_response: Any


class OpenAIService:
    """High-level wrapper responsible for invoking OpenAI models."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: Optional[OpenAI] = None,
        async_client: Optional[AsyncOpenAI] = None,
        cost_estimator: Optional[Callable[[LLMUsage], Optional[float]]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._settings = settings.llm
        self._client = client or OpenAI(timeout=self._settings.request_timeout_seconds)
        self._async_client = async_client or AsyncOpenAI(
            timeout=self._settings.request_timeout_seconds
        )
        self._cost_estimator = cost_estimator
        self._logger = logger or LOGGER

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        cost_estimator: Optional[Callable[[LLMUsage], Optional[float]]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> "OpenAIService":
        """Factory method using project settings for construction."""

        return cls(settings=settings, cost_estimator=cost_estimator, logger=logger)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResult:
        """Synchronously invoke the LLM."""

        return self._run_with_retries(
            prompt=prompt,
            call=self._client.responses.create,
            sleep=time.sleep,
            model_override=model,
            temperature_override=temperature,
            max_tokens_override=max_output_tokens,
        )

    async def agenerate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResult:
        """Asynchronously invoke the LLM."""

        return await self._run_with_retries_async(
            prompt=prompt,
            call=self._async_client.responses.create,
            sleep=asyncio.sleep,
            model_override=model,
            temperature_override=temperature,
            max_tokens_override=max_output_tokens,
        )

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    def _effective_model(self, override: Optional[str]) -> str:
        return override if override is not None else self._settings.model

    def _effective_temperature(self, override: Optional[float]) -> float:
        return (
            override
            if override is not None
            else max(0.0, self._settings.temperature)
        )

    def _effective_max_tokens(self, override: Optional[int]) -> int:
        value = override if override is not None else self._settings.max_output_tokens
        return max(16, value)

    def _log_request(self, model: str, prompt: str, attempt: int) -> None:
        prompt_preview = prompt[:50].replace("\n", " ")
        self._logger.info(
            "OpenAI request attempt=%s model=%s prompt_chars=%s preview=%r",
            attempt,
            model,
            len(prompt),
            prompt_preview + ("…" if len(prompt) > 50 else ""),
        )

    def _handle_usage(self, response: Any) -> LLMUsage:
        usage_data = getattr(response, "usage", None)

        def _get_usage_value(name: str) -> int:
            if usage_data is None:
                return 0
            if isinstance(usage_data, dict):
                value = usage_data.get(name, 0)
            else:
                value = getattr(usage_data, name, 0)
            return int(value or 0)

        usage = LLMUsage(
            prompt_tokens=_get_usage_value("prompt_tokens"),
            completion_tokens=_get_usage_value("completion_tokens"),
            total_tokens=_get_usage_value("total_tokens"),
        )
        if self._cost_estimator:
            try:
                usage_cost = self._cost_estimator(usage)
                object.__setattr__(usage, "cost_usd", usage_cost)
            except Exception as exc:  # pragma: no cover - defensive logging
                self._logger.warning("Cost estimator failed: %s", exc)
        return usage

    def _extract_text(self, response: Any) -> str:
        text = getattr(response, "output_text", None)
        if text is not None:
            return text

        # Fallback for structured content; gather text entries if available.
        content = getattr(response, "output", None) or getattr(response, "content", None)
        segments = []
        if isinstance(content, list):
            for item in content:
                if hasattr(item, "content"):
                    for child in getattr(item, "content", []):
                        text_value = getattr(child, "text", None)
                        if text_value:
                            segments.append(text_value)
                elif hasattr(item, "text"):
                    segments.append(getattr(item, "text"))
        return "\n".join(segments) if segments else ""

    def _should_retry(self, exc: OpenAIError) -> bool:
        status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
        return status_code in {408, 409, 429, 500, 502, 503, 504}

    def _raise_service_error(self, exc: OpenAIError) -> None:
        status_code = getattr(exc, "status_code", None)
        message = getattr(exc, "message", str(exc))
        self._logger.error("OpenAI request failed (status=%s): %s", status_code, message)
        raise OpenAIServiceError(message) from exc

    def _prepare_payload(
        self,
        *,
        prompt: str,
        model_override: Optional[str],
        temperature_override: Optional[float],
        max_tokens_override: Optional[int],
    ) -> dict[str, Any]:
        return {
            "model": self._effective_model(model_override),
            "input": prompt,
            "temperature": self._effective_temperature(temperature_override),
            "max_output_tokens": self._effective_max_tokens(max_tokens_override),
        }

    def _build_result(self, response: Any, payload: dict[str, Any], duration: float) -> LLMResult:
        usage = self._handle_usage(response)
        response_id = getattr(response, "id", None)
        self._logger.info(
            "OpenAI request completed model=%s total_tokens=%s latency=%.2fs",
            payload["model"],
            usage.total_tokens,
            duration,
        )
        text = self._extract_text(response)
        return LLMResult(
            text=text,
            usage=usage,
            model=payload["model"],
            response_id=response_id,
            latency_seconds=duration,
            raw_response=response,
        )

    def _run_with_retries(
        self,
        *,
        prompt: str,
        call: Callable[..., Any],
        sleep: Callable[[float], None],
        model_override: Optional[str],
        temperature_override: Optional[float],
        max_tokens_override: Optional[int],
    ) -> LLMResult:
        payload = self._prepare_payload(
            prompt=prompt,
            model_override=model_override,
            temperature_override=temperature_override,
            max_tokens_override=max_tokens_override,
        )
        for attempt in range(1, self._settings.max_retry_attempts + 1):
            self._log_request(payload["model"], prompt, attempt)
            start = time.perf_counter()
            try:
                response = call(**payload)
                duration = time.perf_counter() - start
                return self._build_result(response, payload, duration)
            except OpenAIError as exc:
                if attempt >= self._settings.max_retry_attempts or not self._should_retry(exc):
                    self._raise_service_error(exc)
                backoff = self._settings.retry_backoff_seconds * (2 ** (attempt - 1))
                self._logger.warning(
                    "OpenAI request retrying in %.2fs (attempt %s/%s): %s",
                    backoff,
                    attempt,
                    self._settings.max_retry_attempts,
                    exc,
                )
                sleep(backoff)
        # Should never be reached because loop will either return or raise.
        raise OpenAIServiceError("OpenAI request failed after retries.")

    async def _run_with_retries_async(
        self,
        *,
        prompt: str,
        call: Callable[..., Any],
        sleep: Callable[[float], asyncio.Future],
        model_override: Optional[str],
        temperature_override: Optional[float],
        max_tokens_override: Optional[int],
    ) -> LLMResult:
        payload = self._prepare_payload(
            prompt=prompt,
            model_override=model_override,
            temperature_override=temperature_override,
            max_tokens_override=max_tokens_override,
        )
        for attempt in range(1, self._settings.max_retry_attempts + 1):
            self._log_request(payload["model"], prompt, attempt)
            start = time.perf_counter()
            try:
                response = await call(**payload)
                duration = time.perf_counter() - start
                return self._build_result(response, payload, duration)
            except OpenAIError as exc:
                if attempt >= self._settings.max_retry_attempts or not self._should_retry(exc):
                    self._raise_service_error(exc)
                backoff = self._settings.retry_backoff_seconds * (2 ** (attempt - 1))
                self._logger.warning(
                    "OpenAI async request retrying in %.2fs (attempt %s/%s): %s",
                    backoff,
                    attempt,
                    self._settings.max_retry_attempts,
                    exc,
                )
                await sleep(backoff)
        raise OpenAIServiceError("OpenAI async request failed after retries.")


def build_default_service(
    *,
    settings: Settings,
    cost_estimator: Optional[Callable[[LLMUsage], Optional[float]]] = None,
    logger: Optional[logging.Logger] = None,
) -> OpenAIService:
    """Convenience helper mirroring `OpenAIService.from_settings`."""

    return OpenAIService.from_settings(
        settings=settings,
        cost_estimator=cost_estimator,
        logger=logger,
    )

