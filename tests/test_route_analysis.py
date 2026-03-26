"""Tests for composite /route-analysis/{route_id} endpoint."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from wko5.api.app import create_app


def _get_client():
    app = create_app(token="test-token")
    return TestClient(app), "test-token"


def _find_valid_route_id(client, token):
    """Find a route ID that exists in the database."""
    resp = client.get("/api/routes", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 200:
        routes = resp.json()
        if isinstance(routes, list) and len(routes) > 0:
            return routes[0].get("id")
    return None


def test_route_analysis_returns_all_sections():
    """Composite endpoint should return route, demand, gap_analysis, opportunity_cost."""
    client, token = _get_client()
    route_id = _find_valid_route_id(client, token)
    if route_id is None:
        # No routes in DB — skip
        return

    resp = client.get(f"/api/route-analysis/{route_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "route" in data
    assert "demand" in data
    assert "gap_analysis" in data
    assert "opportunity_cost" in data


def test_route_analysis_route_has_detail():
    """Route section should contain route detail fields."""
    client, token = _get_client()
    route_id = _find_valid_route_id(client, token)
    if route_id is None:
        return

    resp = client.get(f"/api/route-analysis/{route_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    route = data["route"]
    assert "id" in route
    assert "history" in route
    assert "plans" in route
    assert "points" in route


def test_route_analysis_demand_has_segments_key():
    """Demand section should always include a 'segments' key (even if empty or error)."""
    client, token = _get_client()
    route_id = _find_valid_route_id(client, token)
    if route_id is None:
        return

    resp = client.get(f"/api/route-analysis/{route_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    demand = data["demand"]
    # demand always has segments key, even on error
    assert "segments" in demand


def test_route_analysis_404_unknown():
    """Non-existent route should return 404."""
    client, token = _get_client()
    resp = client.get("/api/route-analysis/999999",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_route_analysis_requires_auth():
    """Endpoint should require authentication."""
    client, _ = _get_client()
    resp = client.get("/api/route-analysis/1")
    assert resp.status_code == 401


def test_route_analysis_json_serializable():
    """Response should be fully JSON serializable (no numpy types leaking)."""
    import json
    client, token = _get_client()
    route_id = _find_valid_route_id(client, token)
    if route_id is None:
        return

    resp = client.get(f"/api/route-analysis/{route_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    # If this doesn't raise, the response is JSON serializable
    data = resp.json()
    # Double-check by re-serializing
    json.dumps(data)
