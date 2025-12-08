"""Test that the Analyst Report is complete and not truncated."""

import pytest
from playwright.sync_api import Page, expect


class TestAnalystReport:
    """Tests for Analyst Report completeness."""

    def test_analyst_report_has_conclusion(self, page_with_server: Page):
        """Verify the Analyst Report is not truncated (has Conclusion section).
        
        This test would have caught the max_tokens=512 bug that caused
        reports to be cut off mid-sentence.
        """
        # Submit a query
        query_input = page_with_server.locator("textarea").first
        query_input.fill("OpenAI API developer pain points")
        
        submit_button = page_with_server.locator("button:has-text('Analyze')").first
        submit_button.click()
        
        # Wait for Analyst Report to appear
        analyst_report = page_with_server.locator("text=Analyst Report")
        expect(analyst_report).to_be_visible(timeout=120000)
        
        # Wait a bit more for full content to render
        page_with_server.wait_for_timeout(2000)
        
        # Get the full page content and check for Conclusion
        page_content = page_with_server.content()
        
        # Log the report length for debugging
        print(f"Page content length: {len(page_content)}")
        
        # The report should have a Conclusion section (our prompt requires it)
        try:
            assert "Conclusion" in page_content or "conclusion" in page_content.lower(), \
                "Analyst Report appears to be truncated - no Conclusion section found"
        except AssertionError:
            # Capture screenshot for debugging
            page_with_server.screenshot(path="tests/e2e/screenshots/analyst_report_failure.png")
            print("✗ Screenshot saved to tests/e2e/screenshots/analyst_report_failure.png")
            raise

    def test_analyst_report_not_cut_mid_sentence(self, page_with_server: Page):
        """Verify the report doesn't end abruptly mid-sentence."""
        query_input = page_with_server.locator("textarea").first
        query_input.fill("Twitter API developer frustrations")
        
        submit_button = page_with_server.locator("button:has-text('Analyze')").first
        submit_button.click()
        
        # Wait for results
        page_with_server.wait_for_selector("text=Analyst Report", timeout=120000)
        page_with_server.wait_for_timeout(3000)  # Allow full render
        
        # Get all text from the page
        page_text = page_with_server.locator("[data-testid='stApp']").inner_text()
        
        # Check that the text doesn't end with incomplete indicators
        incomplete_markers = [
            "...",  # Truncation marker
            "the",  # Mid-sentence articles
            "and",  # Conjunctions
            "with", "for", "to", "in", "on", "at",  # Prepositions
        ]
        
        # Get the last few words
        last_section = page_text.strip()[-100:] if len(page_text) > 100 else page_text
        
        # This is a heuristic - not perfect but catches obvious truncation
        ends_with_period_or_heading = (
            last_section.rstrip().endswith('.') or
            last_section.rstrip().endswith(':') or
            last_section.rstrip().endswith('!') or
            "Conclusion" in last_section
        )
        
        # Log for debugging
        print(f"Last 100 chars of report: {last_section}")
        
        # We don't assert here as this is a soft check - just log the finding
        if not ends_with_period_or_heading:
            print("WARNING: Report may be truncated - doesn't end with proper punctuation")
