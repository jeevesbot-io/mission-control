"""Integration tests for the War Room module."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_warroom():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "warroom" in ids


# ---------------------------------------------------------------------------
# Tasks — list / create / update / delete
# ---------------------------------------------------------------------------

def test_list_tasks_empty():
    with patch("modules.warroom.service.WarRoomService.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/warroom/tasks")
        assert response.status_code == 200
        assert response.json() == []


def test_list_tasks_returns_data():
    from modules.warroom.models import Task

    tasks = [
        Task(
            id="abc1",
            title="Build Security Council",
            description="Agent security framework",
            status="backlog",
            priority="high",
            project="openclaw-platform",
            tags=["security"],
            createdAt="2026-02-01T00:00:00+00:00",
            updatedAt="2026-02-01T00:00:00+00:00",
        )
    ]
    with patch("modules.warroom.service.WarRoomService.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = tasks
        response = client.get("/api/warroom/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Build Security Council"
        assert data[0]["project"] == "openclaw-platform"
        assert data[0]["tags"] == ["security"]


def test_list_tasks_filter_by_project():
    with patch("modules.warroom.service.WarRoomService.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/warroom/tasks?project=matron")
        assert response.status_code == 200
        mock.assert_called_once_with(project="matron", priority=None, tags=None, status=None)


def test_list_tasks_filter_by_priority():
    with patch("modules.warroom.service.WarRoomService.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/warroom/tasks?priority=urgent")
        assert response.status_code == 200
        mock.assert_called_once_with(project=None, priority="urgent", tags=None, status=None)


def test_create_task():
    from modules.warroom.models import Task

    created = Task(
        id="xyz9",
        title="New Task",
        description="",
        status="backlog",
        priority="medium",
        project=None,
        tags=[],
        createdAt="2026-02-18T00:00:00+00:00",
        updatedAt="2026-02-18T00:00:00+00:00",
    )
    with patch("modules.warroom.service.WarRoomService.create_task", new_callable=AsyncMock) as mock:
        mock.return_value = created
        response = client.post("/api/warroom/tasks", json={"title": "New Task"})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "xyz9"
        assert data["title"] == "New Task"


def test_update_task():
    from modules.warroom.models import Task

    updated = Task(
        id="abc1",
        title="Updated",
        status="todo",
        priority="urgent",
        project="job-hunt",
        tags=[],
        createdAt="2026-02-01T00:00:00+00:00",
        updatedAt="2026-02-18T00:00:00+00:00",
    )
    with patch("modules.warroom.service.WarRoomService.update_task", new_callable=AsyncMock) as mock:
        mock.return_value = updated
        response = client.put("/api/warroom/tasks/abc1", json={"title": "Updated", "priority": "urgent"})
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"


def test_update_task_not_found():
    with patch("modules.warroom.service.WarRoomService.update_task", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.put("/api/warroom/tasks/nope", json={"title": "x"})
        assert response.status_code == 404


def test_delete_task():
    with patch("modules.warroom.service.WarRoomService.delete_task", new_callable=AsyncMock) as mock:
        mock.return_value = True
        response = client.delete("/api/warroom/tasks/abc1")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_delete_task_not_found():
    with patch("modules.warroom.service.WarRoomService.delete_task", new_callable=AsyncMock) as mock:
        mock.return_value = False
        response = client.delete("/api/warroom/tasks/nope")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Agent queue protocol (critical — must not break)
# ---------------------------------------------------------------------------

def test_get_queue_returns_sorted_tasks():
    from modules.warroom.models import Task

    tasks = [
        Task(id="1", title="Low priority", status="todo", priority="low", project=None, tags=[],
             createdAt="2026-02-01T00:00:00+00:00", updatedAt="2026-02-01T00:00:00+00:00"),
        Task(id="2", title="Urgent task", status="todo", priority="urgent", project=None, tags=[],
             createdAt="2026-02-01T00:00:00+00:00", updatedAt="2026-02-01T00:00:00+00:00"),
        Task(id="3", title="High priority", status="todo", priority="high", project=None, tags=[],
             createdAt="2026-02-01T00:00:00+00:00", updatedAt="2026-02-01T00:00:00+00:00"),
    ]
    with patch("modules.warroom.service.WarRoomService.get_queue", new_callable=AsyncMock) as mock:
        mock.return_value = [tasks[1], tasks[2], tasks[0]]  # urgent, high, low
        response = client.get("/api/warroom/tasks/queue")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["id"] == "2"  # urgent first
        assert data[1]["id"] == "3"  # high second
        assert data[2]["id"] == "1"  # low last


def test_pickup_task():
    from modules.warroom.models import Task

    picked = Task(
        id="abc1", title="Task", status="in-progress", priority="medium",
        pickedUp=True, project=None, tags=[],
        createdAt="2026-02-01T00:00:00+00:00", updatedAt="2026-02-18T00:00:00+00:00",
    )
    with patch("modules.warroom.service.WarRoomService.pickup_task", new_callable=AsyncMock) as mock:
        mock.return_value = picked
        response = client.post("/api/warroom/tasks/abc1/pickup")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in-progress"
        assert data["pickedUp"] is True


def test_complete_task_with_result():
    from modules.warroom.models import Task

    completed = Task(
        id="abc1", title="Task", status="done", priority="medium",
        result="Successfully completed", project=None, tags=[],
        completedAt="2026-02-18T10:00:00+00:00",
        createdAt="2026-02-01T00:00:00+00:00", updatedAt="2026-02-18T10:00:00+00:00",
    )
    with patch("modules.warroom.service.WarRoomService.complete_task", new_callable=AsyncMock) as mock:
        mock.return_value = completed
        response = client.post("/api/warroom/tasks/abc1/complete", json={"result": "Successfully completed"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["result"] == "Successfully completed"
        assert data["completedAt"] is not None


def test_complete_task_with_error():
    from modules.warroom.models import Task

    failed = Task(
        id="abc1", title="Task", status="done", priority="medium",
        error="Agent crashed", project=None, tags=[],
        completedAt="2026-02-18T10:00:00+00:00",
        createdAt="2026-02-01T00:00:00+00:00", updatedAt="2026-02-18T10:00:00+00:00",
    )
    with patch("modules.warroom.service.WarRoomService.complete_task", new_callable=AsyncMock) as mock:
        mock.return_value = failed
        response = client.post("/api/warroom/tasks/abc1/complete", json={"error": "Agent crashed"})
        assert response.status_code == 200
        assert response.json()["error"] == "Agent crashed"


def test_pickup_task_not_found():
    with patch("modules.warroom.service.WarRoomService.pickup_task", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.post("/api/warroom/tasks/nope/pickup")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

def test_list_projects_with_task_counts():
    from modules.warroom.models import ProjectWithCount

    projects = [
        ProjectWithCount(id="openclaw-platform", name="OpenClaw Platform", icon="Gear",
                         color="red", status="active", order=7, task_count=5),
    ]
    with patch("modules.warroom.service.WarRoomService.list_projects", new_callable=AsyncMock) as mock:
        mock.return_value = projects
        response = client.get("/api/warroom/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["task_count"] == 5
        assert data[0]["id"] == "openclaw-platform"


def test_delete_project_with_tasks_fails():
    with patch("modules.warroom.service.WarRoomService.delete_project", new_callable=AsyncMock) as mock:
        mock.return_value = (False, "Cannot delete project with existing tasks. Reassign or delete tasks first.")
        response = client.delete("/api/warroom/projects/openclaw-platform")
        assert response.status_code == 422
        assert "Cannot delete" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

def test_list_tags_returns_sorted_list():
    with patch("modules.warroom.service.WarRoomService.list_tags", new_callable=AsyncMock) as mock:
        mock.return_value = ["agent", "security", "ui"]
        response = client.get("/api/warroom/tags")
        assert response.status_code == 200
        assert response.json() == ["agent", "security", "ui"]


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

def test_get_usage():
    from modules.warroom.models import UsageResponse, UsageTier

    usage = UsageResponse(
        model="claude-sonnet-4-6",
        tiers=[
            UsageTier(label="Current session", percent=23, resetsIn="3h 45m"),
            UsageTier(label="Current week (all models)", percent=11, resetsIn="6d 12h"),
        ],
    )
    with patch("modules.warroom.service.WarRoomService.get_usage", new_callable=AsyncMock) as mock:
        mock.return_value = usage
        response = client.get("/api/warroom/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "claude-sonnet-4-6"
        assert len(data["tiers"]) == 2
        assert data["tiers"][0]["percent"] == 23


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def test_get_models():
    with patch("modules.warroom.service.WarRoomService.get_models", new_callable=AsyncMock) as mock:
        mock.return_value = ["claude-sonnet-4-6", "claude-opus-4-6"]
        response = client.get("/api/warroom/models")
        assert response.status_code == 200
        assert "claude-sonnet-4-6" in response.json()


def test_set_model():
    from modules.warroom.models import ModelResponse

    with patch("modules.warroom.service.WarRoomService.set_model", new_callable=AsyncMock) as mock:
        mock.return_value = ModelResponse(success=True, model="claude-opus-4-6")
        response = client.post("/api/warroom/model", json={"model": "claude-opus-4-6"})
        assert response.status_code == 200
        assert response.json()["model"] == "claude-opus-4-6"
        assert response.json()["success"] is True


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

def test_get_heartbeat():
    from modules.warroom.models import HeartbeatResponse

    with patch("modules.warroom.service.WarRoomService.get_heartbeat", new_callable=AsyncMock) as mock:
        mock.return_value = HeartbeatResponse(lastHeartbeat=1708000000000)
        response = client.get("/api/warroom/heartbeat")
        assert response.status_code == 200
        assert response.json()["lastHeartbeat"] == 1708000000000


def test_get_heartbeat_null():
    from modules.warroom.models import HeartbeatResponse

    with patch("modules.warroom.service.WarRoomService.get_heartbeat", new_callable=AsyncMock) as mock:
        mock.return_value = HeartbeatResponse(lastHeartbeat=None)
        response = client.get("/api/warroom/heartbeat")
        assert response.status_code == 200
        assert response.json()["lastHeartbeat"] is None


def test_record_heartbeat():
    from modules.warroom.models import HeartbeatResponse

    with patch("modules.warroom.service.WarRoomService.record_heartbeat", new_callable=AsyncMock) as mock:
        mock.return_value = HeartbeatResponse(lastHeartbeat=1708000001000)
        response = client.post("/api/warroom/heartbeat")
        assert response.status_code == 200
        assert response.json()["lastHeartbeat"] == 1708000001000


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

def test_list_skills():
    from modules.warroom.models import Skill

    skills = [
        Skill(id="my-skill", name="My Skill", description="Does things",
              source="workspace", enabled=True, path="/some/path", hasMetadata=True),
    ]
    with patch("modules.warroom.service.WarRoomService.list_skills", new_callable=AsyncMock) as mock:
        mock.return_value = skills
        response = client.get("/api/warroom/skills")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "my-skill"
        assert data[0]["source"] == "workspace"


def test_toggle_skill():
    from modules.warroom.models import Skill

    toggled = Skill(id="my-skill", name="My Skill", description="",
                    source="workspace", enabled=False, path="/some/path")
    with patch("modules.warroom.service.WarRoomService.toggle_skill", new_callable=AsyncMock) as mock:
        mock.return_value = toggled
        response = client.post("/api/warroom/skills/my-skill/toggle", json={"enabled": False})
        assert response.status_code == 200
        assert response.json()["enabled"] is False


# ---------------------------------------------------------------------------
# Workspace files
# ---------------------------------------------------------------------------

def test_get_workspace_file():
    from modules.warroom.models import WorkspaceFileResponse

    with patch("modules.warroom.service.WarRoomService.get_workspace_file", new_callable=AsyncMock) as mock:
        mock.return_value = WorkspaceFileResponse(content="# SOUL.md\nBe helpful.", lastModified="2026-02-18T00:00:00+00:00")
        response = client.get("/api/warroom/workspace-file?name=SOUL.md")
        assert response.status_code == 200
        assert "SOUL.md" in response.json()["content"]


def test_get_workspace_file_invalid_name():
    response = client.get("/api/warroom/workspace-file?name=../../etc/passwd")
    assert response.status_code == 400


def test_update_workspace_file_saves_history():
    with patch("modules.warroom.service.WarRoomService.update_workspace_file", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.put("/api/warroom/workspace-file?name=SOUL.md", json={"content": "# New soul"})
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock.assert_called_once_with("SOUL.md", "# New soul")


def test_workspace_file_history():
    from modules.warroom.models import HistoryEntry

    history = [
        HistoryEntry(timestamp="2026-02-17T00:00:00+00:00", content="# Old soul"),
    ]
    with patch("modules.warroom.service.WarRoomService.get_file_history", new_callable=AsyncMock) as mock:
        mock.return_value = history
        response = client.get("/api/warroom/workspace-file/history?name=SOUL.md")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "# Old soul"


# ---------------------------------------------------------------------------
# Soul templates
# ---------------------------------------------------------------------------

def test_soul_templates_returns_six():
    response = client.get("/api/warroom/soul/templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    names = [t["name"] for t in data]
    assert "Minimal Assistant" in names
    assert "Sarcastic Sidekick" in names


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_get_stats():
    from modules.warroom.models import WarRoomStats

    stats = WarRoomStats(
        in_progress_count=2,
        todo_count=5,
        last_heartbeat=1708000000000,
        active_model="claude-sonnet-4-6",
    )
    with patch("modules.warroom.service.WarRoomService.get_stats", new_callable=AsyncMock) as mock:
        mock.return_value = stats
        response = client.get("/api/warroom/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["in_progress_count"] == 2
        assert data["todo_count"] == 5
        assert data["active_model"] == "claude-sonnet-4-6"
