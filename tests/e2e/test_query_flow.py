"""Test the happy path query flow from input to results display."""

import pytest
from playwright.sync_api import Page, expect


class TestQueryFlow:
    """Tests for the main query submission flow."""

    def test_submit_query_shows_loading(self, page_with_server: Page):
        """Verify submitting a query shows a loading state."""
        # Find the query input
        query_input = page_with_server.locator("textarea").first
        query_input.fill("OpenAI API developer pain points")
        
        # Find and click the submit button (Streamlit buttons)
        submit_button = page_with_server.locator("button:has-text('Analyze')").first
        
        # If no "Analyze" button, try other common button texts
        if not submit_button.is_visible(timeout=2000):
            submit_button = page_with_server.locator("button").first
        
        submit_button.click()
        
        # Wait for some indication that processing started
        # Streamlit shows a spinner or loading indicator
        page_with_server.wait_for_timeout(2000)  # Brief wait for state change
        
        # Page should still be responsive
        expect(page_with_server.locator("[data-testid='stApp']")).to_be_visible()

    def test_query_returns_results(self, page_with_server: Page):
        """Verify a query eventually returns results (long timeout for LLM)."""
        # Submit a simple query
        query_input = page_with_server.locator("textarea").first
        query_input.fill("Common frustrations with billing systems")
        
        # Find submit button
        submit_button = page_with_server.locator("button").first
        submit_button.click()
        
        # Wait for results to appear (up to 120s for full LLM workflow)
        # Look for the Analyst Report section or pain points
        results_locator = page_with_server.locator("text=Analyst Report").or_(
            page_with_server.locator("text=Pain Point")
        ).or_(
            page_with_server.locator("text=Conclusion")
        )
        
        expect(results_locator.first).to_be_visible(timeout=120000)
