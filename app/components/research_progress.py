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
    if "google" in lowered or "search" in lowered or "web" in lowered:
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
        self._is_complete = False
        self._current_source: Dict[str, str] | None = None
        self._recent_sources: List[Dict[str, str]] = []

        self._slot = st.empty()

        self.render()

    def render(self) -> None:
        """Re-render all progress UI elements."""

        pills: list[str] = []
        for step in self._steps:
            state = self._status_by_key.get(step.key, "pending")
            pills.append(
                f"<div class='pp-step pp-step--{state}'><span class='pp-step-icon'>{_safe_text(step.icon)}</span>"
                f"<span class='pp-step-label'>{_safe_text(step.label)}</span></div>"
            )

        source_html = ""
        if self._is_complete:
            source_html = "<div class='pp-progress-source pp-progress-source--done'>Research complete.</div>"
        elif self._current_source:
            domain = _safe_text(self._current_source.get("domain", ""))
            title = _safe_text(self._current_source.get("title", "")) or "Reviewing source…"
            source_html = (
                "<div class='pp-progress-source'>"
                f"<span class='pp-source-domain'>{domain}</span>"
                f"<span class='pp-source-title'>{title}</span>"
                "</div>"
            )
        else:
            source_html = "<div class='pp-progress-source pp-progress-source--empty'>Waiting for sources…</div>"

        recent_html = ""
        if self._recent_sources:
            rows = []
            for source in self._recent_sources[: self._max_recent_sources]:
                rows.append(
                    "<div class='pp-source-row'>"
                    f"<span class='pp-source-chip'>{_safe_text(source.get('icon',''))}</span>"
                    f"<span class='pp-source-row-domain'>{_safe_text(source.get('domain',''))}</span>"
                    f"<span class='pp-source-row-title'>{_safe_text(source.get('title',''))}</span>"
                    "</div>"
                )
            recent_html = (
                "<div class='pp-sources'><div class='pp-sources-title'>Recently checked</div>"
                + "".join(rows)
                + "</div>"
            )

        self._slot.markdown(
            f"""
            <div class="pp-panel">
              <div class="pp-panel-inner">
                <div class="pp-progress-header">
                  <div class="pp-progress-title">Research Progress</div>
                  <div class="pp-progress-eta">Estimated: 30–90s</div>
                </div>
                <div class="pp-progress-status">{_safe_text(self._active_message)}</div>
                <div class='pp-steps'>{''.join(pills)}</div>
                {source_html}
                {recent_html}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def apply_event(self, event: Mapping[str, Any]) -> None:
        """Update the panel based on a progress event emitted by the agent backend."""

        event_type = str(event.get("type") or "")
        if event_type == "stage":
            stage = str(event.get("stage") or "")
            message = str(event.get("message") or "")
            if message:
                self._active_message = message
            self._activate_stage(stage)
            if stage == "complete":
                self._mark_all_done()
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
                self._is_complete = False
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
                    self._ingest_sources(sources, bucket=bucket)

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

    def _mark_all_done(self) -> None:
        for key in list(self._status_by_key.keys()):
            self._status_by_key[key] = "done"
        self._is_complete = True

    def _ingest_sources(self, sources: List[Any], *, bucket: str | None) -> None:
        """Update current/recent sources from real tool output hints."""

        icon = "🌐" if bucket == "web" else "💬" if bucket == "reddit" else "🔎"

        for raw in sources:
            if not isinstance(raw, Mapping):
                continue
            url = str(raw.get("url") or "")
            if not url:
                continue
            title = str(raw.get("title") or "").strip()
            domain = _domain(url)
            if not domain:
                continue
            source_entry = {"domain": domain, "title": title, "icon": icon}
            self._recent_sources = [entry for entry in self._recent_sources if entry.get("domain") != domain]
            self._recent_sources.insert(0, source_entry)
            self._recent_sources = self._recent_sources[: self._max_recent_sources]

        if self._recent_sources:
            top = self._recent_sources[0]
            self._current_source = {"domain": str(top.get("domain", "")), "title": str(top.get("title", ""))}
