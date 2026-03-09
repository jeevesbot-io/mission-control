"""Tests for the Skills Browser module."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


MOCK_SKILLS = [
    {"name": "test-skill", "description": "A test skill", "source": "managed"},
    {"name": "another-skill", "description": "Another skill", "source": "workspace"},
]


def test_list_skills_returns_200():
    with patch("modules.skills.service.skills_browser_service.scan_all", return_value=MOCK_SKILLS):
        response = client.get("/api/skills/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "test-skill"


def test_get_skill_returns_content():
    with patch(
        "modules.skills.service.skills_browser_service.get_skill_content",
        return_value="# Test Skill\nHello",
    ):
        response = client.get("/api/skills/test-skill")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-skill"
    assert data["content"] == "# Test Skill\nHello"


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
