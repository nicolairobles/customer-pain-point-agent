"""Simple runtime health check for the Streamlit deployment."""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request
from typing import Sequence

DEFAULT_URL = "http://localhost:8501/"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe app health and required secrets.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Endpoint to probe for a 2xx/3xx response.")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--allow-missing-secrets",
        action="store_true",
        help="Skip failing on absent API credentials (useful for CI smoke checks).",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _env_flag(key: str, *, default: str = "false") -> bool:
    value = os.getenv(key, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def get_missing_required_keys(allow_missing_secrets: bool) -> list[str]:
    """Return list of required environment variable keys that are not set.

    Args:
        allow_missing_secrets: If True, returns empty list regardless of missing keys.
                             If False, returns list of required keys not found in environment.

    Returns:
        List of missing required key names, or empty list if allow_missing_secrets is True.
    """
    if allow_missing_secrets:
        return []

    required_keys: list[str] = ["OPENAI_API_KEY"]

    if _env_flag("TOOL_REDDIT_ENABLED", default="true"):
        required_keys.extend(["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"])

    if _env_flag("TOOL_GOOGLE_SEARCH_ENABLED", default="true"):
        required_keys.extend(["GOOGLE_SEARCH_API_KEY", "GOOGLE_SEARCH_ENGINE_ID"])

    return [key for key in required_keys if not os.getenv(key)]


def probe_url(url: str, timeout: float) -> int:
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    missing_keys = get_missing_required_keys(args.allow_missing_secrets)
    if missing_keys:
        sys.stderr.write(f"Missing required secrets: {', '.join(missing_keys)}\n")
        sys.stderr.flush()
        return 1

    try:
        status = probe_url(args.url, args.timeout)
    except urllib.error.URLError as exc:
        sys.stderr.write(f"Health probe connection failed: {exc.reason}\n")
        sys.stderr.flush()
        return 1
    except TimeoutError as exc:
        sys.stderr.write(f"Health probe timed out after {args.timeout}s: {exc}\n")
        sys.stderr.flush()
        return 1
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"Health probe failed with unexpected error: {exc}\n")
        sys.stderr.flush()
        return 1

    if status < 200 or status >= 400:
        sys.stderr.write(f"Health probe returned HTTP {status}\n")
        sys.stderr.flush()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
