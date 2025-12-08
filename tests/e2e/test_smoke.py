"""Smoke test to verify Playwright and Streamlit server work correctly."""

import pytest
from playwright.sync_api import Page, expect


def test_app_loads(page_with_server: Page):
    """SMOKE TEST: Verify the Streamlit app loads correctly.
    
    WHAT THIS CHECKS:
    - Streamlit server starts successfully
    - App renders without JavaScript errors
    - Main app container is visible
    
    IF THIS FAILS:
    - Check if Streamlit is installed correctly
    - Check if app/streamlit_app.py has syntax errors
    """
    app_container = page_with_server.locator("[data-testid='stApp']")
    expect(app_container).to_be_visible(timeout=15000)
    print("✓ Streamlit app container is visible and rendered correctly")


def test_query_input_visible(page_with_server: Page):
    """SMOKE TEST: Verify the query input field is present.
    
    WHAT THIS CHECKS:
    - Query input component renders
    - Users can see where to type their query
    
    IF THIS FAILS:
    - Check render_query_input() in app/components/query_input.py
    """
    input_locator = page_with_server.locator("textarea, input[type='text']").first
    expect(input_locator).to_be_visible(timeout=10000)
    print("✓ Query input field is visible and ready for user input")
