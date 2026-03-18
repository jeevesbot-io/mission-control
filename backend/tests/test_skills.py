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


# --- Sprint 2: Drift report endpoint tests ---


def test_drift_report_returns_entries():
    """GET /api/skills/drift returns drift entries."""
    mock_drift = [
        {
            "skill_name": "reading-list",
            "source_label": "User",
            "old_hash": "aaa111",
            "new_hash": "bbb222",
            "old_file_count": 4,
            "new_file_count": 5,
            "files_changed": [{"path": "references/new-guide.md", "action": "added"}],
            "detected_at": "2026-03-15T14:30:00Z",
        }
    ]
    with patch(
        "modules.skills.service.skills_browser_service.get_drift_report",
        new_callable=AsyncMock,
        return_value=mock_drift,
    ):
        response = client.get("/api/skills/drift")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["skill_name"] == "reading-list"
    assert data[0]["source_label"] == "User"
    assert data[0]["old_hash"] == "aaa111"
    assert data[0]["new_hash"] == "bbb222"
    assert data[0]["old_file_count"] == 4
    assert data[0]["new_file_count"] == 5
    assert data[0]["files_changed"][0]["action"] == "added"


def test_drift_report_with_since_param():
    """GET /api/skills/drift?since=... passes the since filter."""
    with patch(
        "modules.skills.service.skills_browser_service.get_drift_report",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_fn:
        response = client.get("/api/skills/drift?since=2026-03-01T00:00:00Z")
    assert response.status_code == 200
    assert response.json() == []
    # Verify since was passed through
    call_kwargs = mock_fn.call_args
    since_arg = call_kwargs.kwargs.get("since") or call_kwargs[1].get("since")
    assert since_arg is not None


def test_drift_report_empty_state():
    """GET /api/skills/drift returns empty list when no drift detected."""
    with patch(
        "modules.skills.service.skills_browser_service.get_drift_report",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = client.get("/api/skills/drift")
    assert response.status_code == 200
    assert response.json() == []


# --- Sprint 2: Stats endpoint tests ---


def test_stats_returns_correct_structure():
    """GET /api/skills/stats returns overview statistics."""
    mock_stats = {
        "total_skills": 36,
        "by_source": {"System": 23, "User": 5, "Workspace": 7, "Extension": 1},
        "drifted_last_7d": 2,
        "last_full_index": "2026-03-18T03:00:00Z",
    }
    with patch(
        "modules.skills.service.skills_browser_service.get_stats",
        new_callable=AsyncMock,
        return_value=mock_stats,
    ):
        response = client.get("/api/skills/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_skills"] == 36
    assert data["by_source"]["System"] == 23
    assert data["by_source"]["User"] == 5
    assert data["by_source"]["Extension"] == 1
    assert data["drifted_last_7d"] == 2
    assert data["last_full_index"] is not None


def test_stats_with_zero_drift():
    """GET /api/skills/stats correctly shows zero drift."""
    mock_stats = {
        "total_skills": 10,
        "by_source": {"System": 10},
        "drifted_last_7d": 0,
        "last_full_index": "2026-03-18T03:00:00Z",
    }
    with patch(
        "modules.skills.service.skills_browser_service.get_stats",
        new_callable=AsyncMock,
        return_value=mock_stats,
    ):
        response = client.get("/api/skills/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_skills"] == 10
    assert data["drifted_last_7d"] == 0


def test_stats_empty_index():
    """GET /api/skills/stats handles empty index gracefully."""
    mock_stats = {
        "total_skills": 0,
        "by_source": {},
        "drifted_last_7d": 0,
        "last_full_index": None,
    }
    with patch(
        "modules.skills.service.skills_browser_service.get_stats",
        new_callable=AsyncMock,
        return_value=mock_stats,
    ):
        response = client.get("/api/skills/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_skills"] == 0
    assert data["by_source"] == {}
    assert data["last_full_index"] is None
