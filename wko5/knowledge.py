"""Thin HTTP client for qmd knowledge service."""

import httpx
import logging

log = logging.getLogger(__name__)


class KnowledgeClient:
    """Queries qmd's MCP-over-HTTP endpoint."""

    _HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    def __init__(self, base_url: str = "http://localhost:8181"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self._session_id: str | None = None
        self._req_id = 0

    def _ensure_session(self) -> bool:
        """Initialize MCP session if needed."""
        if self._session_id:
            return True
        try:
            resp = httpx.post(self.mcp_url, headers=self._HEADERS, json={
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "wko5", "version": "1.0"},
                },
            }, timeout=10.0)
            resp.raise_for_status()
            self._session_id = resp.headers.get("mcp-session-id")
            return self._session_id is not None
        except Exception as e:
            log.warning("qmd session init failed: %s", e)
            return False

    def _call(self, method: str, params: dict) -> dict | None:
        """Send an MCP tools/call request."""
        if not self._ensure_session():
            return None
        try:
            self._req_id += 1
            headers = {**self._HEADERS, "Mcp-Session-Id": self._session_id}
            resp = httpx.post(self.mcp_url, headers=headers, json={
                "jsonrpc": "2.0",
                "id": self._req_id,
                "method": "tools/call",
                "params": {
                    "name": method,
                    "arguments": params,
                },
            }, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            log.warning("qmd unavailable: %s", e)
            self._session_id = None
            return None

    def search(self, query: str, collections: list[str] | None = None,
               limit: int = 10, min_score: float = 0.3) -> dict | None:
        """Hybrid search across knowledge base."""
        params = {
            "searches": [
                {"type": "lex", "query": query},
                {"type": "vec", "query": query},
            ],
            "limit": limit,
            "minScore": min_score,
            "rerank": True,
        }
        if collections:
            params["collections"] = collections
        return self._call("query", params)

    def get_document(self, path: str) -> dict | None:
        """Retrieve a specific document by path."""
        return self._call("get", {"path": path})

    def health(self) -> bool:
        """Check if qmd service is running."""
        try:
            resp = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
