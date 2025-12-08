"""Smoke test to verify Playwright and Streamlit server work correctly."""

import pytest
from playwright.sync_api import Page, expect


def test_app_loads(page_with_server: Page):
    """Verify the Streamlit app loads and displays the main container."""
    # Streamlit apps have a main app container
    app_container = page_with_server.locator("[data-testid='stApp']")
    expect(app_container).to_be_visible(timeout=15000)


def test_query_input_visible(page_with_server: Page):
    """Verify the query input is visible on the page."""
    # Look for text input or textarea in Streamlit
    input_locator = page_with_server.locator("textarea, input[type='text']").first
    expect(input_locator).to_be_visible(timeout=10000)
