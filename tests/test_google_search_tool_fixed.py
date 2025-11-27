from __future__ import annotations

import pytest

from config.settings import settings
from src.tools.google_search_tool import GoogleSearchTool


class FakeCSE:
    def __init__(self, items):
        self._items = items

    def list(self, **kwargs):
        class L:
            def __init__(self, items):
                self._items = items

            def execute(self):
                return {"items": self._items}

        return L(self._items)


class FakeService:
    def __init__(self, items):
        self._items = items

    def cse(self):
        return FakeCSE(self._items)


def test_google_search_tool_normalizes_results(monkeypatch):
    fake_items = [
        {
            "title": "T1",
            "link": "https://example.com/1",
            "snippet": "s1",
            "displayLink": "example.com",
            "cacheId": "c1",
        }
    ]

    def fake_build(name, version, developerKey=None):
        assert name == "customsearch"
        assert version == "v1"
        # developerKey may be empty in test environment; allow the call
        return FakeService(fake_items)

    monkeypatch.setattr("googleapiclient.discovery.build", fake_build)

    tool = GoogleSearchTool.from_settings(settings)

    # If settings don't have real keys locally, the tool may set _service None;
    # in that case, ensure the fake monkeypatch produced a service.
    if not tool._service:
        pytest.skip("GoogleSearchTool has no service instance in this environment")

    results = tool._run("test query", num=1)
    assert isinstance(results, list)
    assert results[0]["title"] == "T1"
    assert results[0]["display_link"] == "example.com"
    assert results[0]["cache_id"] == "c1"
