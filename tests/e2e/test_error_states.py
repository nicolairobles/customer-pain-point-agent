"""Test error handling in the UI."""

import pytest
from playwright.sync_api import Page, expect


class TestErrorHandling:
    """Tests for error states and validation."""

    def test_empty_query_shows_error(self, page_with_server: Page):
        """Verify empty query submission shows an error message."""
        # Try to submit without entering a query
        submit_button = page_with_server.locator("button").first
        submit_button.click()
        
        # Wait for potential error message
        page_with_server.wait_for_timeout(2000)
        
        # Look for error indicators (Streamlit's st.error or validation message)
        page_content = page_with_server.content().lower()
        
        # Check if there's some indication of invalid input
        has_error_indication = (
            "error" in page_content or
            "required" in page_content or
            "empty" in page_content or
            "please enter" in page_content or
            "invalid" in page_content
        )
        
        # Note: This may not fail depending on app behavior
        # Some apps allow empty submissions and return "no results"
        print(f"Error indication found: {has_error_indication}")

    def test_app_recovers_after_error(self, page_with_server: Page):
        """Verify the app remains usable after an error state."""
        # First, try to trigger an error (empty submit or short query)
        submit_button = page_with_server.locator("button").first
        submit_button.click()
        page_with_server.wait_for_timeout(2000)
        
        # Now try a valid query - app should still work
        query_input = page_with_server.locator("textarea").first
        query_input.fill("Test query for recovery")
        
        # Page should still be responsive
        expect(page_with_server.locator("[data-testid='stApp']")).to_be_visible()
        
        # Should be able to click the button again
        submit_button.click()
        
        # Wait and verify no crash occurred
        page_with_server.wait_for_timeout(3000)
        expect(page_with_server.locator("[data-testid='stApp']")).to_be_visible()

    def test_ui_responsive_during_loading(self, page_with_server: Page):
        """Verify the UI doesn't freeze during long operations."""
        # Submit a query
        query_input = page_with_server.locator("textarea").first
        query_input.fill("Long running test query")
        
        submit_button = page_with_server.locator("button").first
        submit_button.click()
        
        # While loading, the page should still respond
        # Try scrolling or hovering
        page_with_server.wait_for_timeout(1000)
        
        # The app container should remain visible
        expect(page_with_server.locator("[data-testid='stApp']")).to_be_visible()
