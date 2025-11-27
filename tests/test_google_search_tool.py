from __future__ import annotations

import sys
import types

import pytest

from config.settings import APISettings, Settings
from src.tools import google_search_tool as google_module
from src.tools.google_search_tool import GoogleSearchTool


def _install_google_client(monkeypatch, fake_service):
    """Register a fake googleapiclient module tree returning `fake_service`."""

    discovery_module = types.ModuleType("googleapiclient.discovery")

    def fake_build(name, version, developerKey=None):
        assert name == "customsearch"
        assert version == "v1"
        return fake_service

    discovery_module.build = fake_build

    errors_module = types.ModuleType("googleapiclient.errors")

    class FakeHttpError(Exception):
        pass

    errors_module.HttpError = FakeHttpError

    root_module = types.ModuleType("googleapiclient")
    root_module.discovery = discovery_module
    root_module.errors = errors_module

    monkeypatch.setitem(sys.modules, "googleapiclient", root_module)
    monkeypatch.setitem(sys.modules, "googleapiclient.discovery", discovery_module)
    monkeypatch.setitem(sys.modules, "googleapiclient.errors", errors_module)
    monkeypatch.setattr(google_module, "HttpError", FakeHttpError, raising=False)

    return FakeHttpError


def _make_settings(api_key: str = "fake-key", cse_id: str = "fake-cx") -> Settings:
    return Settings(api=APISettings(google_search_api_key=api_key, google_search_engine_id=cse_id))


class RecordingService:
    def __init__(self, items=None, error=None):
        self._items = items or []
        self._error = error
        self.last_kwargs = None

    def cse(self):
        service = self

        class FakeCSE:
            def list(self, **kwargs):
                service.last_kwargs = kwargs

                class FakeRequest:
                    def execute(inner_self):
                        if service._error:
                            raise service._error
                        return {"items": service._items}

                return FakeRequest()

        return FakeCSE()


def test_google_search_tool_normalizes_results(monkeypatch):
    items = [
        {
            "title": "T1",
            "link": "https://example.com/1",
            "snippet": "s1",
            "displayLink": "example.com",
            "cacheId": "c1",
        }
    ]
    service = RecordingService(items=items)
    _install_google_client(monkeypatch, service)

    tool = GoogleSearchTool.from_settings(_make_settings())
    results = tool._run("query")

    assert results == [
        {
            "title": "T1",
            "link": "https://example.com/1",
            "snippet": "s1",
            "display_link": "example.com",
            "cache_id": "c1",
        }
    ]


def test_google_search_tool_limits_num_parameter(monkeypatch):
    service = RecordingService()
    _install_google_client(monkeypatch, service)

    tool = GoogleSearchTool.from_settings(_make_settings())

    tool._run("query", num=25)
    assert service.last_kwargs["num"] == 10

    tool._run("query", num=-5)
    assert service.last_kwargs["num"] == 1


def test_google_search_tool_raises_when_credentials_missing():
    tool = GoogleSearchTool.from_settings(_make_settings(api_key="", cse_id=""))

    with pytest.raises(RuntimeError):
        tool._run("query")


def test_google_search_tool_wraps_http_errors(monkeypatch):
    service = RecordingService()
    fake_http_error = _install_google_client(monkeypatch, service)
    service._error = fake_http_error("boom")

    tool = GoogleSearchTool.from_settings(_make_settings())

    with pytest.raises(RuntimeError) as excinfo:
        tool._run("query")

    assert "Google Custom Search request failed" in str(excinfo.value)


def test_google_search_tool_handles_empty_items(monkeypatch):
    service = RecordingService(items=[])
    _install_google_client(monkeypatch, service)

    tool = GoogleSearchTool.from_settings(_make_settings())
    assert tool._run("query") == []
