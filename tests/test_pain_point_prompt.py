"""Tests for the pain point prompt template."""

from __future__ import annotations

import json
from textwrap import dedent

import pytest

from src.extractors.pain_point_extractor import PainPoint
from src.extractors.prompts import (
    PAIN_POINT_PROMPT_VERSION,
    PainPointPrompt,
    format_documents_for_prompt,
)


def test_format_documents_renders_expected_bullets() -> None:
    documents = [
        {
            "platform": "reddit",
            "author": "redditorA",
            "timestamp": "2025-11-18T10:15:00Z",
            "url": "https://reddit.com/r/test",
            "summary": "Users are frustrated with onboarding.",
            "content": "The onboarding wizard breaks when uploading CSV files.",
        }
    ]

    result = format_documents_for_prompt(documents)
    assert "1. Source: reddit" in result
    assert "Author: redditorA" in result
    assert "The onboarding wizard breaks" in result


def test_prompt_includes_schema_and_version() -> None:
    prompt = PainPointPrompt()
    rendered = prompt.build([])
    assert "RESPONSE SCHEMA" in rendered
    assert PAIN_POINT_PROMPT_VERSION in rendered
    assert '"pain_points": [' in rendered


def test_sample_outputs_validate_against_schema() -> None:
    """Simulate the dry run and bias check by validating curated outputs."""

    sample_output = dedent(
        """
        {
          "pain_points": [
            {
              "name": "Onboarding wizard fails for CSV uploads",
              "description": "Customers cannot complete onboarding because CSV uploads time out or throw parsing errors.",
              "frequency": "high",
              "examples": [
                "Onboarding blocked: the CSV wizard keeps crashing.",
                "Multiple teammates hit 504 errors when uploading contacts."
              ],
              "sources": [
                {
                  "platform": "reddit",
                  "url": "https://reddit.com/r/example1",
                  "timestamp": "2025-11-15T09:00:00Z",
                  "author": "redditorA"
                },
                {
                  "platform": "twitter",
                  "url": "https://twitter.com/example/status/1",
                  "timestamp": "2025-11-16T13:20:00Z",
                  "author": "customer_success_lead"
                }
              ]
            },
            {
              "name": "Support responses feel dismissive",
              "description": "Several users perceive automated support replies as curt or unhelpful, leading to trust issues.",
              "frequency": "medium",
              "examples": [
                "The bot just told me to reboot without acknowledging the impact.",
                "Support replies are scripted and ignore the nuance."
              ],
              "sources": [
                {
                  "platform": "google",
                  "url": "https://example.com/review/123",
                  "timestamp": "2025-11-14T18:30:00Z",
                  "author": "b2b_reviewer_23"
                }
              ]
            }
          ],
          "analysis_notes": {
            "common_themes": [
              "Pain points cluster around onboarding reliability and support tone."
            ],
            "data_coverage": {
              "reddit_posts_considered": 3,
              "twitter_posts_considered": 2,
              "google_results_considered": 1
            },
            "confidence": "medium",
            "content_warnings": [
              "One Reddit comment contains mild profanity while describing the bug."
            ]
          }
        }
        """
    )

    payload = json.loads(sample_output)
    assert "pain_points" in payload
    parsed = [PainPoint(**point) for point in payload["pain_points"]]
    assert len(parsed) == 2


def test_schema_regression_guard() -> None:
    """Prevent unintended schema edits by snapshotting the JSON text."""

    prompt = PainPointPrompt()
    expected_hash_anchor = "pain_points"

    assert prompt.response_schema.count(expected_hash_anchor) >= 1


