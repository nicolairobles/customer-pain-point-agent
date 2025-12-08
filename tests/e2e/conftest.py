"""Playwright E2E test fixtures and configuration."""

import subprocess
import time
import socket
import pytest
from typing import Generator


def _find_available_port(start: int = 8501, end: int = 8599) -> int:
    """Find an available port in the given range."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available ports in range {start}-{end}")


def _wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for the server to be ready."""
    import requests
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def streamlit_server() -> Generator[str, None, None]:
    """Start and stop a Streamlit server for E2E tests.
    
    Yields:
        The URL of the running Streamlit server (e.g., "http://localhost:8501")
    """
    port = _find_available_port()
    url = f"http://localhost:{port}"
    
    # Start Streamlit in headless mode
    proc = subprocess.Popen(
        [
            ".venv/bin/streamlit", "run", "app/streamlit_app.py",
            "--server.headless=true",
            f"--server.port={port}",
            "--server.fileWatcherType=none",  # Disable file watcher for stability
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=".",  # Run from project root
    )
    
    # Wait for server to be ready
    if not _wait_for_server(url, timeout=30):
        proc.terminate()
        proc.wait()
        raise RuntimeError(f"Streamlit server failed to start on {url}")
    
    yield url
    
    # Cleanup
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="function")
def page_with_server(page, streamlit_server):
    """Navigate to the Streamlit app before each test."""
    page.goto(streamlit_server)
    page.wait_for_load_state("networkidle")
    return page
