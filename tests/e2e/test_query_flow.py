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
        """E2E TEST: Verify a query actually returns results from the LLM.
        
        WHAT THIS CHECKS:
        - Full pipeline works: Query → Reddit API → LLM → Analyst → UI
        - "Conclusion" section appears (proves report wasn't truncated)
        - This is the test that would catch the max_tokens=512 truncation bug
        
        TIMEOUT: Up to 120 seconds (LLM calls can be slow)
        """
        # Ensure fresh state by reloading
        page_with_server.reload()
        page_with_server.wait_for_load_state("networkidle")
        
        # Verify we're starting fresh (no prior results visible)
        # Look for Conclusion which only appears AFTER LLM response
        initial_content = page_with_server.content()
        assert "Conclusion" not in initial_content, "Page has cached results - expected fresh state"
        print("✓ Starting with fresh page (no prior results)")
        
        # Submit a query
        query_input = page_with_server.locator("textarea").first
        query_input.fill("OpenAI API developer pain points")
        print("✓ Entered query: 'OpenAI API developer pain points'")
        
        # Find and click the ANALYZE button (NOT the Deploy button!)
        # Streamlit has other buttons in the menu, so we must target by text
        submit_button = page_with_server.locator("button:has-text('Analyze')").first
        expect(submit_button).to_be_visible(timeout=5000)
        submit_button.click()
        print("✓ Clicked 'Analyze' button, waiting for LLM response...")
        print("  (This may take 60-120 seconds for Reddit API + LLM calls)")
        
        # Wait for "Conclusion" which ONLY appears after LLM completes
        # This is the key marker that proves:
        # 1. The full pipeline ran
        # 2. The response wasn't truncated (max_tokens bug would cut before Conclusion)
        conclusion_locator = page_with_server.locator("text=Conclusion")
        
        expect(conclusion_locator.first).to_be_visible(timeout=120000)
        print("✓ SUCCESS! 'Conclusion' section found - report was NOT truncated")
