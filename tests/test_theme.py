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

