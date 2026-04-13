import importlib.util
import os
import pytest
from unittest.mock import patch, MagicMock

# Import knowledge module directly to avoid wko5/__init__.py dependency chain
_spec = importlib.util.spec_from_file_location(
    "wko5.knowledge",
    os.path.join(os.path.dirname(__file__), "..", "wko5", "knowledge.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
KnowledgeClient = _mod.KnowledgeClient


def test_search_returns_results():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"content": [{"text": "...results..."}]}}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response) as mock_post:
        client = KnowledgeClient(base_url="http://localhost:8181")
        results = client.search("FTP testing protocols")
        assert results is not None
        assert mock_post.call_count == 2  # init session + query


def test_search_with_collection_filter():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"content": [{"text": "..."}]}}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response) as mock_post:
        client = KnowledgeClient(base_url="http://localhost:8181")
        results = client.search("glycogen depletion", collections=["nutrition", "wiki"])
        assert results is not None
        # Verify collections were passed
        call_args = mock_post.call_args
        body = call_args.kwargs.get("json") or call_args[1].get("json")
        assert body["params"]["arguments"]["collections"] == ["nutrition", "wiki"]


def test_search_handles_unavailable_service():
    with patch("httpx.post", side_effect=Exception("Connection refused")):
        client = KnowledgeClient(base_url="http://localhost:8181")
        results = client.search("anything")
        assert results is None


def test_health_returns_true_when_running():
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.get", return_value=mock_response):
        client = KnowledgeClient()
        assert client.health() is True


def test_health_returns_false_when_down():
    with patch("httpx.get", side_effect=Exception("Connection refused")):
        client = KnowledgeClient()
        assert client.health() is False


def test_get_document():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"content": [{"text": "doc content"}]}}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response):
        client = KnowledgeClient()
        result = client.get_document("wiki/concepts/ftp.md")
        assert result is not None
