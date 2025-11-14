#!/usr/bin/env python3
"""Smoke test for verifying OpenAI API connectivity using project credentials."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from time import perf_counter

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


def mask_secret(value: str) -> str:
    """Return a partially masked representation of a secret for safe logging."""

    if not value:
        return "<empty>"
    visible = value[:4]
    return f"{visible}{'*' * max(0, len(value) - 4)}"


def configure_logging(verbose: bool) -> None:
    """Configure the root logger with a friendly format and log level."""

    level = logging.DEBUG if verbose else logging.INFO
    # Timestamped logs make it easier to share results in project tracking tools.
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the smoke test."""

    parser = argparse.ArgumentParser(
        description="Verify connectivity to the OpenAI API using project credentials.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model to ping during the smoke test (default: %(default)s)",
    )
    parser.add_argument(
        "--prompt",
        default="Quick connectivity check.",
        help="Optional prompt for the test completion request.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=32,
        help="Upper bound for response tokens (must be >= 16). Default: %(default)s",
    )
    # Timeout can save cost by preventing hung requests from running indefinitely.
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Request timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging for troubleshooting.",
    )
    return parser.parse_args()


def load_configuration() -> str:
    """Load environment variables and return the OpenAI API key."""

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "")
    logging.debug("Loaded OPENAI_API_KEY=%s", mask_secret(api_key))
    if not api_key:
        logging.error(
            "OPENAI_API_KEY is missing. Ensure it is defined in your .env file before running the smoke test."
        )
        sys.exit(1)
    return api_key


def perform_smoke_test(model: str, prompt: str, timeout: float, max_output_tokens: int) -> None:
    """Issue a lightweight completion request to confirm API reachability."""

    client = OpenAI(timeout=timeout)
    # Keep the prompt tiny so we minimise token spend but still exercise the API.
    logging.info("Requesting completion from model=%s", model)
    start = perf_counter()

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max(16, max_output_tokens),
        )
    except OpenAIError as exc:
        logging.exception("OpenAI API call failed: %s", exc)
        logging.error(
            "Double-check your network connectivity, API key permissions, and model availability."
        )
        sys.exit(1)

    duration = perf_counter() - start
    logging.info("Received response in %.2f seconds", duration)
    logging.info("Response ID: %s", getattr(response, "id", "<unknown>"))
    logging.debug("Raw response payload: %s", response)
    logging.info("Smoke test succeeded.")


def main() -> None:
    """Entry point for the script."""

    args = parse_args()
    configure_logging(args.verbose)
    load_configuration()
    perform_smoke_test(args.model, args.prompt, args.timeout, args.max_output_tokens)


if __name__ == "__main__":
    main()
