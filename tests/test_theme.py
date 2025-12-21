"""Smoke tests for theme helpers."""

from __future__ import annotations

from app import theme


def test_get_global_css_contains_tokens() -> None:
    """Global CSS should expose the expected variables."""

    css = theme.get_global_css()

    assert "<style>" in css
    assert "--color-background" in css
    assert "--color-accent" in css
    assert "stAppViewContainer" in css


def test_apply_global_styles_injects_css_every_render(monkeypatch) -> None:
    """Global styles must be injected on rerun-triggered renders."""

    calls: list[str] = []

    def fake_markdown(value: str, unsafe_allow_html: bool = False) -> None:
        assert unsafe_allow_html is True
        calls.append(value)

    monkeypatch.setattr(theme.st, "markdown", fake_markdown)

    theme.apply_global_styles()
    theme.apply_global_styles()

    assert len(calls) == 2
