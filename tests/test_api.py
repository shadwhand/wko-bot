import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from wko5.api.app import create_app


def _get_client():
    app = create_app(token="test-secret-token")
    return TestClient(app), "test-secret-token"


def test_health_no_auth():
    client, _ = _get_client()
    response = client.get("/api/health")
    assert response.status_code == 200


def test_fitness_requires_auth():
    client, _ = _get_client()
    response = client.get("/api/fitness")
    assert response.status_code == 401


def test_fitness_with_auth():
    client, token = _get_client()
    response = client.get("/api/fitness", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "CTL" in data
    assert "ATL" in data
    assert "TSB" in data


def test_activities_with_auth():
    client, token = _get_client()
    response = client.get("/api/activities?start=2025-01-01&end=2025-12-31",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_model_with_auth():
    client, token = _get_client()
    response = client.get("/api/model?days=90",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "mFTP" in data


def test_config_get():
    client, token = _get_client()
    response = client.get("/api/config", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "weight_kg" in data
    assert data["weight_kg"] == 78.0
