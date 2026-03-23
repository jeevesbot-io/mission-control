"""Integration tests for the Workspace module."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_workspace():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "workspace" in ids


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------


def test_get_heartbeat():
    from modules.workspace.models import HeartbeatResponse

    with patch("modules.workspace.service.get_heartbeat", new_callable=AsyncMock) as mock:
        mock.return_value = HeartbeatResponse(lastHeartbeat=1708000000000)
        response = client.get("/api/workspace/heartbeat")
        assert response.status_code == 200
        assert response.json()["lastHeartbeat"] == 1708000000000


def test_get_heartbeat_null():
    from modules.workspace.models import HeartbeatResponse

    with patch("modules.workspace.service.get_heartbeat", new_callable=AsyncMock) as mock:
        mock.return_value = HeartbeatResponse(lastHeartbeat=None)
        response = client.get("/api/workspace/heartbeat")
        assert response.status_code == 200
        assert response.json()["lastHeartbeat"] is None


def test_record_heartbeat():
    from modules.workspace.models import HeartbeatResponse

    with patch("modules.workspace.service.record_heartbeat", new_callable=AsyncMock) as mock:
        mock.return_value = HeartbeatResponse(lastHeartbeat=1708000001000)
        response = client.post("/api/workspace/heartbeat")
        assert response.status_code == 200
        assert response.json()["lastHeartbeat"] == 1708000001000


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------


def test_get_usage():
    from modules.workspace.models import UsageResponse, UsageTier

    usage = UsageResponse(
        model="claude-sonnet-4-6",
        tiers=[
            UsageTier(label="Current session", percent=23, resetsIn="3h 45m"),
            UsageTier(label="Current week (all models)", percent=11, resetsIn="6d 12h"),
        ],
    )
    with patch("modules.workspace.service.get_usage", new_callable=AsyncMock) as mock:
        mock.return_value = usage
        response = client.get("/api/workspace/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "claude-sonnet-4-6"
        assert len(data["tiers"]) == 2
        assert data["tiers"][0]["percent"] == 23


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def test_get_models():
    with patch("modules.workspace.service.get_models", new_callable=AsyncMock) as mock:
        mock.return_value = ["claude-sonnet-4-6", "claude-opus-4-6"]
        response = client.get("/api/workspace/models")
        assert response.status_code == 200
        assert "claude-sonnet-4-6" in response.json()


def test_set_model():
    from modules.workspace.models import ModelResponse

    with patch("modules.workspace.service.set_model", new_callable=AsyncMock) as mock:
        mock.return_value = ModelResponse(success=True, model="claude-opus-4-6")
        response = client.post("/api/workspace/model", json={"model": "claude-opus-4-6"})
        assert response.status_code == 200
        assert response.json()["model"] == "claude-opus-4-6"
        assert response.json()["success"] is True


# ---------------------------------------------------------------------------
# Workspace files
# ---------------------------------------------------------------------------


def test_get_workspace_file():
    from modules.workspace.models import WorkspaceFileResponse

    with patch("modules.workspace.service.get_workspace_file", new_callable=AsyncMock) as mock:
        mock.return_value = WorkspaceFileResponse(
            content="# SOUL.md\nBe helpful.",
            lastModified="2026-02-18T00:00:00+00:00",
        )
        response = client.get("/api/workspace/workspace-file?name=SOUL.md")
        assert response.status_code == 200
        assert "SOUL.md" in response.json()["content"]


def test_get_workspace_file_invalid_name():
    response = client.get("/api/workspace/workspace-file?name=../../etc/passwd")
    assert response.status_code == 400


def test_get_workspace_file_identity():
    from modules.workspace.models import WorkspaceFileResponse

    with patch("modules.workspace.service.get_workspace_file", new_callable=AsyncMock) as mock:
        mock.return_value = WorkspaceFileResponse(
            content="# IDENTITY.md\nI am an agent.",
            lastModified="2026-03-01T00:00:00+00:00",
        )
        response = client.get("/api/workspace/workspace-file?name=IDENTITY.md")
        assert response.status_code == 200
        assert "IDENTITY.md" in response.json()["content"]


def test_update_workspace_file_saves_history():
    with patch("modules.workspace.service.update_workspace_file", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.put(
            "/api/workspace/workspace-file?name=SOUL.md",
            json={"content": "# New soul"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock.assert_called_once_with("SOUL.md", "# New soul")


def test_update_workspace_file_invalid_name():
    response = client.put(
        "/api/workspace/workspace-file?name=EVIL.md",
        json={"content": "# hack"},
    )
    assert response.status_code == 400


def test_workspace_file_history():
    from modules.workspace.models import HistoryEntry

    history = [
        HistoryEntry(timestamp="2026-02-17T00:00:00+00:00", content="# Old soul"),
    ]
    with patch("modules.workspace.service.get_file_history", new_callable=AsyncMock) as mock:
        mock.return_value = history
        response = client.get("/api/workspace/workspace-file/history?name=SOUL.md")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "# Old soul"


def test_workspace_file_history_invalid_name():
    response = client.get("/api/workspace/workspace-file/history?name=BAD.md")
    assert response.status_code == 400


def test_revert_workspace_file():
    from modules.workspace.models import WorkspaceFileResponse

    with patch("modules.workspace.service.revert_workspace_file", new_callable=AsyncMock) as mock:
        mock.return_value = WorkspaceFileResponse(
            content="# Reverted soul",
            lastModified="2026-03-01T00:00:00+00:00",
        )
        response = client.post(
            "/api/workspace/workspace-file/revert?name=SOUL.md",
            json={"index": 0},
        )
        assert response.status_code == 200
        assert response.json()["content"] == "# Reverted soul"


def test_revert_workspace_file_invalid_index():
    with patch("modules.workspace.service.revert_workspace_file", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.post(
            "/api/workspace/workspace-file/revert?name=SOUL.md",
            json={"index": 999},
        )
        assert response.status_code == 400
        assert "Invalid history index" in response.json()["detail"]


def test_revert_workspace_file_invalid_name():
    response = client.post(
        "/api/workspace/workspace-file/revert?name=BAD.md",
        json={"index": 0},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Soul templates
# ---------------------------------------------------------------------------


def test_soul_templates_returns_six():
    response = client.get("/api/workspace/soul/templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    names = [t["name"] for t in data]
    assert "Minimal Assistant" in names
    assert "Sarcastic Sidekick" in names


def test_soul_templates_have_required_fields():
    response = client.get("/api/workspace/soul/templates")
    assert response.status_code == 200
    for template in response.json():
        assert "name" in template
        assert "description" in template
        assert "content" in template
        assert len(template["content"]) > 0


# ---------------------------------------------------------------------------
# Filename validation
# ---------------------------------------------------------------------------


def test_validate_workspace_filename_allowed():
    from modules.workspace.service import validate_workspace_filename

    assert validate_workspace_filename("SOUL.md") is True
    assert validate_workspace_filename("IDENTITY.md") is True
    assert validate_workspace_filename("USER.md") is True
    assert validate_workspace_filename("AGENTS.md") is True


def test_validate_workspace_filename_rejected():
    from modules.workspace.service import validate_workspace_filename

    assert validate_workspace_filename("../../etc/passwd") is False
    assert validate_workspace_filename("README.md") is False
    assert validate_workspace_filename("") is False
    assert validate_workspace_filename("soul.md") is False  # case-sensitive


# ---------------------------------------------------------------------------
# Usage computation (unit tests with mocked file I/O)
# ---------------------------------------------------------------------------


def test_format_duration_hours_minutes():
    from modules.workspace.service import _format_duration

    assert _format_duration(5 * 3600 * 1000) == "5h 0m"
    assert _format_duration(3600 * 1000 + 30 * 60 * 1000) == "1h 30m"
    assert _format_duration(0) == "0h 0m"


def test_format_duration_days():
    from modules.workspace.service import _format_duration

    assert _format_duration(7 * 24 * 3600 * 1000) == "7d 0h"
    assert _format_duration(2 * 24 * 3600 * 1000 + 3 * 3600 * 1000) == "2d 3h"


def test_compute_usage_no_sessions_dir():
    """When sessions directory doesn't exist, usage should be 0%."""
    from unittest.mock import MagicMock, PropertyMock

    from modules.workspace.service import _compute_usage_sync

    mock_path = MagicMock()
    mock_path.exists.return_value = False

    mock_openclaw_json = MagicMock()
    mock_openclaw_json.read_text.side_effect = FileNotFoundError

    with patch("modules.workspace.service.settings") as mock_settings:
        type(mock_settings).sessions_path = PropertyMock(return_value=mock_path)
        mock_oc_path = MagicMock()
        mock_oc_path.__truediv__ = MagicMock(return_value=mock_openclaw_json)
        type(mock_settings).openclaw_path = PropertyMock(return_value=mock_oc_path)

        result = _compute_usage_sync()
        assert result.tiers[0].percent == 0
        assert result.tiers[1].percent == 0
        assert result.model == "unknown"
