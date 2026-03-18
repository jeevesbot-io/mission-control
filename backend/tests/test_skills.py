"""Tests for the Skills Browser module."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


MOCK_SKILLS = [
    {"name": "test-skill", "description": "A test skill", "source": "User", "source_label": "User"},
    {
        "name": "another-skill",
        "description": "Another skill",
        "source": "Workspace",
        "source_label": "Workspace",
    },
]


def test_list_skills_returns_200():
    """List skills — mock both DB (empty) and filesystem fallback."""
    with (
        patch(
            "modules.skills.service.skills_browser_service.list_from_db",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "modules.skills.service.skills_browser_service.scan_all",
            return_value=MOCK_SKILLS,
        ),
    ):
        response = client.get("/api/skills/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "test-skill"


def test_list_skills_from_db():
    """List skills serves from DB when data exists."""
    db_skills = [
        {
            "id": 1,
            "name": "weather",
            "description": "Get weather",
            "source": "System",
            "source_label": "System",
            "file_count": 1,
            "sha256_hash": "abc123",
            "last_indexed_at": "2026-03-18T00:00:00Z",
            "last_changed_at": None,
            "has_drift": False,
        }
    ]
    with patch(
        "modules.skills.service.skills_browser_service.list_from_db",
        new_callable=AsyncMock,
        return_value=db_skills,
    ):
        response = client.get("/api/skills/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "weather"
    assert data[0]["source_label"] == "System"


def test_get_skill_returns_content():
    with (
        patch(
            "modules.skills.service.skills_browser_service.get_skill_content",
            return_value="# Test Skill\nHello",
        ),
        patch(
            "modules.skills.service.skills_browser_service.get_skill_detail_from_db",
            new_callable=AsyncMock,
            return_value={
                "sha256_hash": "abc123",
                "last_changed_at": None,
                "source_label": "System",
            },
        ),
    ):
        response = client.get("/api/skills/test-skill")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-skill"
    assert data["content"] == "# Test Skill\nHello"
    assert data["sha256_hash"] == "abc123"


def test_get_skill_not_found():
    with patch(
        "modules.skills.service.skills_browser_service.get_skill_content",
        return_value=None,
    ):
        response = client.get("/api/skills/nonexistent")
    assert response.status_code == 404


def test_path_traversal_rejected():
    """Skill names with path separators must not reach the filesystem."""
    with patch(
        "modules.skills.service.skills_browser_service.get_skill_content",
        wraps=lambda name: None,
    ):
        response = client.get("/api/skills/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 404


def test_reindex_endpoint():
    """POST /api/skills/reindex triggers indexer and returns result."""
    mock_reindex_result = {
        "indexed": 36,
        "drifted": 2,
        "new": 0,
        "removed": 0,
        "duration_ms": 150,
    }
    with patch(
        "modules.skills.router.run_reindex",
        new_callable=AsyncMock,
        return_value=mock_reindex_result,
    ):
        response = client.post("/api/skills/reindex")
    assert response.status_code == 200
    data = response.json()
    assert data["indexed"] == 36
    assert data["drifted"] == 2
    assert data["duration_ms"] == 150
