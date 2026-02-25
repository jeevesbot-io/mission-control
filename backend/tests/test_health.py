from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# All active module IDs expected to be registered
EXPECTED_MODULE_IDS = {
    "memory", "agents", "school", "calendar", "chat",
    "content", "office", "overview", "warroom", "activity",
}


def test_health_returns_200():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_response_includes_database_field():
    """Response must include a boolean 'database' field."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert isinstance(data["database"], bool)


def test_health_response_version_is_string():
    """Version field must be a non-empty string."""
    response = client.get("/api/health")
    data = response.json()
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


def test_health_returns_degraded_on_db_error():
    """Should return status='degraded' and database=False when the DB is unreachable."""
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("connection refused")

    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("main.async_session", return_value=mock_cm):
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] is False


def test_modules_includes_memory():
    response = client.get("/api/modules")
    assert response.status_code == 200
    modules = response.json()
    ids = [m["id"] for m in modules]
    assert "memory" in ids


def test_modules_lists_all_active_modules():
    """All expected active module IDs must be present."""
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = {m["id"] for m in response.json()}
    assert EXPECTED_MODULE_IDS <= ids


def test_modules_response_has_required_fields():
    """Every module entry must expose id, name, icon, and prefix."""
    response = client.get("/api/modules")
    assert response.status_code == 200
    for module in response.json():
        assert "id" in module
        assert "name" in module
        assert "icon" in module
        assert "prefix" in module
