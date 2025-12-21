"""Streamlit component for Perplexity-style research progress feedback."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping
from urllib.parse import urlparse

import streamlit as st


@dataclass
class ProgressStep:
    key: str
    label: str
    icon: str


_DEFAULT_STEPS: List[ProgressStep] = [
    ProgressStep("planning", "Plan", "🧠"),
    ProgressStep("reddit", "Reddit", "💬"),
    ProgressStep("web", "Web", "🌐"),
    ProgressStep("dedupe", "Dedupe", "🧬"),
    ProgressStep("extract", "Extract", "🧾"),
    ProgressStep("synthesize", "Report", "✨"),
]


def _platform_bucket(tool_name: str) -> str | None:
    lowered = tool_name.lower()
    if "reddit" in lowered:
        return "reddit"
    if "google" in lowered or "search" in lowered:
        return "web"
    return None


def _safe_text(value: Any) -> str:
    return html.escape(str(value or ""), quote=False)


def _domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.netloc or ""
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


class ResearchProgressPanel:
    """Renders a narrated, step-based progress panel for agent runs."""

    def __init__(self, *, steps: List[ProgressStep] | None = None, max_recent_sources: int = 6) -> None:
        self._steps = steps or list(_DEFAULT_STEPS)
        self._max_recent_sources = max_recent_sources
        self._status_by_key: Dict[str, str] = {step.key: "pending" for step in self._steps}
        self._active_message = "Preparing…"
        self._current_source: Dict[str, str] | None = None
        self._recent_sources: List[Dict[str, str]] = []

        self._status_slot = st.empty()
        self._steps_slot = st.empty()
        self._source_slot = st.empty()
        self._recent_slot = st.empty()

        self.render()

    def render(self) -> None:
        """Re-render all progress UI elements."""

        self._status_slot.markdown(
            f"""
            <div class="pp-progress">
              <div class="pp-progress-header">
                <div class="pp-progress-title">Research Progress</div>
                <div class="pp-progress-eta">Estimated: 30–90s</div>
              </div>
              <div class="pp-progress-status">{_safe_text(self._active_message)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pills: list[str] = []
        for step in self._steps:
            state = self._status_by_key.get(step.key, "pending")
            pills.append(
                f"<div class='pp-step pp-step--{state}'><span class='pp-step-icon'>{_safe_text(step.icon)}</span>"
                f"<span class='pp-step-label'>{_safe_text(step.label)}</span></div>"
            )
        self._steps_slot.markdown(
            f"<div class='pp-steps'>{''.join(pills)}</div>",
            unsafe_allow_html=True,
        )

        if self._current_source:
            domain = _safe_text(self._current_source.get("domain", ""))
            title = _safe_text(self._current_source.get("title", "")) or "Reviewing source…"
            self._source_slot.markdown(
                f"<div class='pp-progress-source'><span class='pp-source-domain'>{domain}</span>"
                f"<span class='pp-source-title'>{title}</span></div>",
                unsafe_allow_html=True,
            )
        else:
            self._source_slot.markdown(
                "<div class='pp-progress-source pp-progress-source--empty'>Waiting for sources…</div>",
                unsafe_allow_html=True,
            )

        if self._recent_sources:
            rows = []
            for source in self._recent_sources[: self._max_recent_sources]:
                rows.append(
                    f"<div class='pp-source-row'><span class='pp-source-chip'>{_safe_text(source.get('icon',''))}</span>"
                    f"<span class='pp-source-row-domain'>{_safe_text(source.get('domain',''))}</span>"
                    f"<span class='pp-source-row-title'>{_safe_text(source.get('title',''))}</span></div>"
                )
            self._recent_slot.markdown(
                "<div class='pp-sources'><div class='pp-sources-title'>Recently checked</div>"
                + "".join(rows)
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            self._recent_slot.empty()

    def apply_event(self, event: Mapping[str, Any]) -> None:
        """Update the panel based on a progress event emitted by the agent backend."""

        event_type = str(event.get("type") or "")
        if event_type == "stage":
            stage = str(event.get("stage") or "")
            message = str(event.get("message") or "")
            if message:
                self._active_message = message
            self._activate_stage(stage)
            self.render()
            return

        if event_type == "retry":
            attempt = event.get("attempt")
            self._active_message = f"Retrying (attempt {attempt})…"
            self.render()
            return

        if event_type in {"tool_start", "tool_end", "tool_error"}:
            tool = str(event.get("tool") or "")
            bucket = _platform_bucket(tool)
            if bucket:
                self._activate_stage(bucket)

            if event_type == "tool_start":
                self._active_message = f"Searching {tool}…"
                self.render()
                return

            if event_type == "tool_error":
                self._active_message = f"{tool} failed; continuing…"
                self._mark_done(bucket)
                self.render()
                return

            if event_type == "tool_end":
                sources = event.get("sources") or []
                if isinstance(sources, list) and sources:
                    raw = sources[0]
                    if isinstance(raw, Mapping):
                        url = str(raw.get("url") or "")
                        title = str(raw.get("title") or "")
                        domain = _domain(url)
                        if domain:
                            icon = "🌐" if bucket == "web" else "💬"
                            self._current_source = {"domain": domain, "title": title}
                            self._recent_sources.insert(0, {"domain": domain, "title": title, "icon": icon})
                            self._recent_sources = self._recent_sources[: self._max_recent_sources]

                self._active_message = f"Finished {tool}."
                self._mark_done(bucket)
                self.render()
                return

        if event_type == "warning":
            message = str(event.get("message") or "")
            if message:
                self._active_message = message
                self.render()

    def _activate_stage(self, stage: str) -> None:
        if not stage:
            return
        for key in list(self._status_by_key.keys()):
            if self._status_by_key[key] == "active":
                self._status_by_key[key] = "done"
        if stage in self._status_by_key:
            self._status_by_key[stage] = "active"

    def _mark_done(self, stage: str | None) -> None:
        if stage and stage in self._status_by_key:
            self._status_by_key[stage] = "done"
