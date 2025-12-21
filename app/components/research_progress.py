"""Streamlit component for Perplexity-style research progress feedback."""

from __future__ import annotations

import html
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, MutableMapping
from urllib.parse import urlparse

import streamlit as st


@dataclass
class ProgressStep:
    key: str
    label: str
    icon: str


@dataclass
class _ToolState:
    label: str
    icon: str
    status: str  # idle|running|done|error
    count: int | None = None
    last_updated: float = 0.0


_DEFAULT_STEPS: List[ProgressStep] = [
    ProgressStep("planning", "Plan", "🧠"),
    ProgressStep("research", "Search", "🔎"),
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


def _pretty_tool(tool: str) -> str:
    cleaned = tool.replace("_", " ").strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else "Tool"


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


def _now() -> float:
    return time.monotonic()


class ResearchProgressPanel:
    """Renders a narrated, stable progress panel for agent runs."""

    def __init__(
        self,
        *,
        steps: List[ProgressStep] | None = None,
        max_recent_sources: int = 6,
        max_activity: int = 10,
        min_render_interval_seconds: float = 0.35,
        min_stage_seconds: float = 1.2,
    ) -> None:
        self._steps = steps or list(_DEFAULT_STEPS)
        self._max_recent_sources = max_recent_sources
        self._max_activity = max_activity
        self._min_render_interval_seconds = min_render_interval_seconds
        self._min_stage_seconds = min_stage_seconds

        self._status_by_key: Dict[str, str] = {step.key: "pending" for step in self._steps}
        self._active_message = "Preparing…"
        self._is_complete = False

        self._current_source: Dict[str, str] | None = None
        self._recent_sources: List[Dict[str, str]] = []
        self._activity: List[Dict[str, str]] = []

        self._current_stage: str = "planning"
        self._stage_started_at = _now()
        self._pending_stage: str | None = None
        self._pending_message: str | None = None

        self._tool_states: MutableMapping[str, _ToolState] = {
            "reddit": _ToolState(label="Reddit", icon="💬", status="idle"),
            "web": _ToolState(label="Web", icon="🌐", status="idle"),
        }

        self._slot = st.empty()
        self._last_rendered_at = 0.0

        self._set_stage("planning", message="Planning search…")

    def tick(self) -> None:
        """Allow time-based transitions (debounced stage switching) without new events."""

        self._maybe_flush_pending_stage()

    def render(self) -> None:
        """Re-render all progress UI elements (throttled)."""

        now = _now()
        if (now - self._last_rendered_at) < self._min_render_interval_seconds:
            return
        self._last_rendered_at = now

        pills: list[str] = []
        for step in self._steps:
            state = self._status_by_key.get(step.key, "pending")
            pills.append(
                "<div class='pp-step pp-step--{state}'>"
                "<span class='pp-step-dot'></span>"
                "<span class='pp-step-label'>{label}</span>"
                "</div>".format(state=_safe_text(state), label=_safe_text(step.label))
            )

        tool_chips: list[str] = []
        for key in ("reddit", "web"):
            tool_state = self._tool_states.get(key)
            if tool_state is None:
                continue
            badge = ""
            if tool_state.count is not None:
                badge = f"<span class='pp-chip-count'>{tool_state.count}</span>"
            tool_chips.append(
                "<div class='pp-chip pp-chip--{status}'>"
                "<span class='pp-chip-label'>{label}</span>"
                "{badge}"
                "</div>".format(
                    status=_safe_text(tool_state.status),
                    label=_safe_text(tool_state.label),
                    badge=badge,
                )
            )

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
            any_tool_activity = any(state.status != "idle" for state in self._tool_states.values())
            source_html = (
                "<div class='pp-progress-source pp-progress-source--empty'>Collecting results…</div>"
                if any_tool_activity
                else "<div class='pp-progress-source pp-progress-source--empty'>Preparing sources…</div>"
            )

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

        activity_html = ""
        if self._activity:
            entries = []
            for entry in self._activity[-self._max_activity :]:
                entries.append(
                    "<div class='pp-activity-row'>"
                    f"<span class='pp-activity-text'>{_safe_text(entry.get('text',''))}</span>"
                    "</div>"
                )
            activity_html = (
                "<div class='pp-activity'><div class='pp-activity-title'>Activity</div>" + "".join(entries) + "</div>"
            )

        # IMPORTANT: avoid leading indentation; Markdown treats indented blocks as code.
        panel_html = (
            "<div class=\"pp-panel\">"
            "<div class=\"pp-panel-inner\">"
            "<div class=\"pp-progress-header\">"
            "<div class=\"pp-progress-title\">Research Progress</div>"
            "<div class=\"pp-progress-eta\">Estimated: 30–90s</div>"
            "</div>"
            f"<div class=\"pp-progress-status\">{_safe_text(self._active_message)}</div>"
            f"<div class='pp-steps'>{''.join(pills)}</div>"
            f"<div class='pp-chips'>{''.join(tool_chips)}</div>"
            f"{source_html}"
            f"{recent_html}"
            f"{activity_html}"
            "</div></div>"
        )
        self._slot.markdown(panel_html, unsafe_allow_html=True)

    def apply_event(self, event: Mapping[str, Any]) -> None:
        """Update the panel based on a progress event emitted by the agent backend."""

        self._maybe_flush_pending_stage()

        event_type = str(event.get("type") or "")
        if event_type == "stage":
            stage = str(event.get("stage") or "")
            message = str(event.get("message") or "")
            self._request_stage(stage, message=message or None)
            return

        if event_type == "retry":
            attempt = event.get("attempt")
            self._active_message = f"Retrying (attempt {attempt})…"
            self._push_activity(f"Retrying (attempt {attempt})")
            self.render()
            return

        if event_type in {"tool_start", "tool_end", "tool_error"}:
            tool = str(event.get("tool") or "")
            pretty = _pretty_tool(tool)
            bucket = _platform_bucket(tool)

            # Tool events are sub-events of the stable "research" stage.
            if self._current_stage not in {"research", "dedupe", "extract", "synthesize"}:
                self._request_stage("research", message="Searching sources…")

            if event_type == "tool_start":
                self._active_message = f"Searching {pretty}…"
                if bucket and bucket in self._tool_states:
                    self._tool_states[bucket].status = "running"
                    self._tool_states[bucket].last_updated = _now()
                self._push_activity(f"Searching {pretty}")
                self.render()
                return

            if event_type == "tool_error":
                self._active_message = f"{pretty} failed; continuing…"
                if bucket and bucket in self._tool_states:
                    self._tool_states[bucket].status = "error"
                    self._tool_states[bucket].last_updated = _now()
                self._push_activity(f"{pretty} error")
                self.render()
                return

            if event_type == "tool_end":
                count = event.get("count")
                if bucket and bucket in self._tool_states:
                    self._tool_states[bucket].status = "done"
                    self._tool_states[bucket].last_updated = _now()
                    if isinstance(count, int):
                        self._tool_states[bucket].count = count

                sources = event.get("sources") or []
                if isinstance(sources, list) and sources:
                    self._ingest_sources(sources, bucket=bucket)

                if isinstance(count, int):
                    self._active_message = f"Searched {pretty} ({count} results)"
                    self._push_activity(f"Searched {pretty} ({count})")
                else:
                    self._active_message = f"Searched {pretty}"
                    self._push_activity(f"Searched {pretty}")
                self.render()
                return

        if event_type == "warning":
            message = str(event.get("message") or "")
            if message:
                self._active_message = message
                self._push_activity(message)
                self.render()

    def _request_stage(self, stage: str, *, message: str | None) -> None:
        if not stage:
            return
        if stage != self._current_stage and (_now() - self._stage_started_at) < self._min_stage_seconds:
            self._pending_stage = stage
            self._pending_message = message
            return
        self._set_stage(stage, message=message)

    def _maybe_flush_pending_stage(self) -> None:
        if self._pending_stage is None:
            return
        if (_now() - self._stage_started_at) < self._min_stage_seconds:
            return
        stage = self._pending_stage
        message = self._pending_message
        self._pending_stage = None
        self._pending_message = None
        self._set_stage(stage, message=message)

    def _set_stage(self, stage: str, *, message: str | None) -> None:
        self._current_stage = stage
        self._stage_started_at = _now()
        if message:
            self._active_message = message

        if stage == "complete":
            self._mark_all_done()
        else:
            self._is_complete = False

        for step in self._steps:
            if self._status_by_key[step.key] == "active":
                self._status_by_key[step.key] = "done"
        for step in self._steps:
            if step.key == stage:
                self._status_by_key[step.key] = "active"
            elif self._status_by_key[step.key] != "done":
                self._status_by_key[step.key] = "pending"

        activity_map = {
            "planning": "Planning search",
            "research": "Searching sources",
            "dedupe": "Deduplicating & scoring",
            "extract": "Extracting pain points",
            "synthesize": "Writing report",
            "complete": "Complete",
        }
        if stage in activity_map:
            self._push_activity(activity_map[stage])

        self.render()

    def _mark_all_done(self) -> None:
        for step in self._steps:
            self._status_by_key[step.key] = "done"
        self._is_complete = True
        for tool_state in self._tool_states.values():
            if tool_state.status == "running":
                tool_state.status = "done"

    def _ingest_sources(self, sources: List[Any], *, bucket: str | None) -> None:
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

    def _push_activity(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        if self._activity and self._activity[-1].get("text") == cleaned:
            return
        self._activity.append({"text": cleaned})
        if len(self._activity) > (self._max_activity * 3):
            self._activity = self._activity[-(self._max_activity * 3) :]
