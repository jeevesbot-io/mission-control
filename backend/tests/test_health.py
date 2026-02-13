from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_modules_includes_memory():
    response = client.get("/api/modules")
    assert response.status_code == 200
    modules = response.json()
    ids = [m["id"] for m in modules]
    assert "memory" in ids
