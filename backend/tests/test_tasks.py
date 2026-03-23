"""Integration tests for the Tasks module (Postgres-backed)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_tasks():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "tasks" in ids


# ---------------------------------------------------------------------------
# List tasks
# ---------------------------------------------------------------------------


def test_list_tasks_empty():
    with patch("modules.tasks.service.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        assert response.json() == []


def test_list_tasks_returns_data():
    from modules.tasks.models import Task

    tasks = [
        Task(
            id="42",
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
    with patch("modules.tasks.service.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = tasks
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Build Security Council"
        assert data[0]["id"] == "42"
        assert data[0]["project"] == "openclaw-platform"
        assert data[0]["tags"] == ["security"]
        assert data[0]["priority"] == "high"


def test_list_tasks_filter_by_project():
    with patch("modules.tasks.service.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/tasks/?project=matron")
        assert response.status_code == 200
        mock.assert_called_once_with(project="matron", priority=None, tags=None, status=None)


def test_list_tasks_filter_by_priority():
    with patch("modules.tasks.service.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/tasks/?priority=urgent")
        assert response.status_code == 200
        mock.assert_called_once_with(project=None, priority="urgent", tags=None, status=None)


def test_list_tasks_filter_by_status():
    with patch("modules.tasks.service.list_tasks", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/tasks/?status=in-progress")
        assert response.status_code == 200
        mock.assert_called_once_with(project=None, priority=None, tags=None, status="in-progress")


# ---------------------------------------------------------------------------
# Create task
# ---------------------------------------------------------------------------


def test_create_task():
    from modules.tasks.models import Task

    created = Task(
        id="99",
        title="New Task",
        description="",
        status="backlog",
        priority="medium",
        project=None,
        tags=[],
        slug="new-task",
        createdAt="2026-02-18T00:00:00+00:00",
        updatedAt="2026-02-18T00:00:00+00:00",
    )
    with (
        patch("modules.tasks.service.create_task", new_callable=AsyncMock) as mock_create,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock_create.return_value = created
        response = client.post("/api/tasks/", json={"title": "New Task"})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "99"
        assert data["title"] == "New Task"
        assert data["slug"] == "new-task"
        assert data["priority"] == "medium"
        assert data["status"] == "backlog"


def test_create_task_missing_title():
    """Should return 422 when title is missing."""
    response = client.post("/api/tasks/", json={})
    assert response.status_code == 422


def test_create_task_with_priority_and_status():
    from modules.tasks.models import Task

    created = Task(
        id="100",
        title="Urgent Thing",
        status="todo",
        priority="urgent",
        project="mc",
        tags=["infra"],
        slug="urgent-thing",
        createdAt="2026-02-18T00:00:00+00:00",
        updatedAt="2026-02-18T00:00:00+00:00",
    )
    with (
        patch("modules.tasks.service.create_task", new_callable=AsyncMock) as mock_create,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock_create.return_value = created
        response = client.post(
            "/api/tasks/",
            json={
                "title": "Urgent Thing",
                "priority": "urgent",
                "status": "todo",
                "project": "mc",
                "tags": ["infra"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "urgent"
        assert data["status"] == "todo"
        assert data["project"] == "mc"


def test_create_task_validation_error():
    with (
        patch("modules.tasks.service.create_task", new_callable=AsyncMock) as mock_create,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock_create.side_effect = ValueError("Invalid priority: extreme")
        response = client.post("/api/tasks/", json={"title": "Bad", "priority": "medium"})
        # Note: the ValueError is raised by service, not pydantic validation
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update task
# ---------------------------------------------------------------------------


def test_update_task():
    from modules.tasks.models import Task

    updated = Task(
        id="42",
        title="Updated Title",
        status="todo",
        priority="urgent",
        project="job-hunt",
        tags=[],
        createdAt="2026-02-01T00:00:00+00:00",
        updatedAt="2026-02-18T00:00:00+00:00",
    )
    with (
        patch("modules.tasks.service.update_task", new_callable=AsyncMock) as mock_update,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock_update.return_value = updated
        response = client.put(
            "/api/tasks/42", json={"title": "Updated Title", "priority": "urgent"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"


def test_update_task_not_found():
    with (
        patch("modules.tasks.service.update_task", new_callable=AsyncMock) as mock_update,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock_update.return_value = None
        response = client.put("/api/tasks/999", json={"title": "x"})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete task
# ---------------------------------------------------------------------------


def test_delete_task():
    with (
        patch("modules.tasks.service.delete_task", new_callable=AsyncMock) as mock_delete,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock_delete.return_value = True
        response = client.delete("/api/tasks/42")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_delete_task_not_found():
    with (
        patch("modules.tasks.service.delete_task", new_callable=AsyncMock) as mock_delete,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock_delete.return_value = False
        response = client.delete("/api/tasks/999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


def test_get_queue_returns_sorted_tasks():
    from modules.tasks.models import Task

    tasks = [
        Task(
            id="2",
            title="Urgent task",
            status="todo",
            priority="urgent",
            project=None,
            tags=[],
            createdAt="2026-02-01T00:00:00+00:00",
            updatedAt="2026-02-01T00:00:00+00:00",
        ),
        Task(
            id="3",
            title="High priority",
            status="todo",
            priority="high",
            project=None,
            tags=[],
            createdAt="2026-02-01T00:00:00+00:00",
            updatedAt="2026-02-01T00:00:00+00:00",
        ),
        Task(
            id="1",
            title="Low priority",
            status="todo",
            priority="low",
            project=None,
            tags=[],
            createdAt="2026-02-01T00:00:00+00:00",
            updatedAt="2026-02-01T00:00:00+00:00",
        ),
    ]
    with patch("modules.tasks.service.get_queue", new_callable=AsyncMock) as mock:
        mock.return_value = tasks
        response = client.get("/api/tasks/queue")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["id"] == "2"  # urgent first
        assert data[1]["id"] == "3"  # high second
        assert data[2]["id"] == "1"  # low last


# ---------------------------------------------------------------------------
# Pickup
# ---------------------------------------------------------------------------


def test_pickup_task():
    from modules.tasks.models import Task

    picked = Task(
        id="42",
        title="Task",
        status="in-progress",
        priority="medium",
        pickedUp=True,
        project=None,
        tags=[],
        createdAt="2026-02-01T00:00:00+00:00",
        updatedAt="2026-02-18T00:00:00+00:00",
    )
    with (
        patch("modules.tasks.service.pickup_task", new_callable=AsyncMock) as mock,
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock.return_value = picked
        response = client.post("/api/tasks/42/pickup")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in-progress"
        assert data["pickedUp"] is True


def test_pickup_task_not_found():
    with (
        patch("modules.tasks.service.pickup_task", new_callable=AsyncMock) as mock,
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock.return_value = None
        response = client.post("/api/tasks/999/pickup")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Complete
# ---------------------------------------------------------------------------


def test_complete_task_with_result():
    from modules.tasks.models import Task

    completed = Task(
        id="42",
        title="Task",
        status="done",
        priority="medium",
        result="Successfully completed",
        project=None,
        tags=[],
        completedAt="2026-02-18T10:00:00+00:00",
        createdAt="2026-02-01T00:00:00+00:00",
        updatedAt="2026-02-18T10:00:00+00:00",
    )
    with (
        patch("modules.tasks.service.complete_task", new_callable=AsyncMock) as mock,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock.return_value = completed
        response = client.post("/api/tasks/42/complete", json={"result": "Successfully completed"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["result"] == "Successfully completed"
        assert data["completedAt"] is not None


def test_complete_task_with_error():
    from modules.tasks.models import Task

    failed = Task(
        id="42",
        title="Task",
        status="done",
        priority="medium",
        error="Agent crashed",
        project=None,
        tags=[],
        completedAt="2026-02-18T10:00:00+00:00",
        createdAt="2026-02-01T00:00:00+00:00",
        updatedAt="2026-02-18T10:00:00+00:00",
    )
    with (
        patch("modules.tasks.service.complete_task", new_callable=AsyncMock) as mock,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock.return_value = failed
        response = client.post("/api/tasks/42/complete", json={"error": "Agent crashed"})
        assert response.status_code == 200
        assert response.json()["error"] == "Agent crashed"


def test_complete_task_not_found():
    with (
        patch("modules.tasks.service.complete_task", new_callable=AsyncMock) as mock,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock.return_value = None
        response = client.post("/api/tasks/999/complete", json={"result": "done"})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


def test_list_tags_returns_sorted_list():
    with patch("modules.tasks.service.list_tags", new_callable=AsyncMock) as mock:
        mock.return_value = ["agent", "security", "ui"]
        response = client.get("/api/tasks/tags")
        assert response.status_code == 200
        assert response.json() == ["agent", "security", "ui"]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def test_get_stats():
    from modules.tasks.models import TaskStats

    stats = TaskStats(
        in_progress_count=2,
        todo_count=5,
        last_heartbeat=None,
        active_model="unknown",
    )
    with patch("modules.tasks.service.get_stats", new_callable=AsyncMock) as mock:
        mock.return_value = stats
        response = client.get("/api/tasks/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["in_progress_count"] == 2
        assert data["todo_count"] == 5
        assert data["last_heartbeat"] is None
        assert data["active_model"] == "unknown"


# ---------------------------------------------------------------------------
# Slug generation (unit tests for the helper)
# ---------------------------------------------------------------------------


def test_slug_generation():
    from modules.tasks.service import _generate_slug

    assert _generate_slug("Build Security Council") == "build-security-council"
    assert _generate_slug("Hello  World!!") == "hello-world"
    assert _generate_slug("  Leading and Trailing  ") == "leading-and-trailing"
    # Max length truncation
    long_title = "A" * 100
    assert len(_generate_slug(long_title)) <= 50


def test_slug_special_characters():
    from modules.tasks.service import _generate_slug

    assert _generate_slug("Fix bug #123 — urgent!") == "fix-bug-123-urgent"
    assert _generate_slug("API/v2 endpoint") == "apiv2-endpoint"


# ---------------------------------------------------------------------------
# Priority mapping (unit tests)
# ---------------------------------------------------------------------------


def test_priority_str_to_int():
    from modules.tasks.models import PRIORITY_STR_TO_INT

    assert PRIORITY_STR_TO_INT["urgent"] == 1
    assert PRIORITY_STR_TO_INT["high"] == 2
    assert PRIORITY_STR_TO_INT["medium"] == 3
    assert PRIORITY_STR_TO_INT["low"] == 4


def test_priority_int_to_str():
    from modules.tasks.models import PRIORITY_INT_TO_STR

    assert PRIORITY_INT_TO_STR[1] == "urgent"
    assert PRIORITY_INT_TO_STR[2] == "high"
    assert PRIORITY_INT_TO_STR[3] == "medium"
    assert PRIORITY_INT_TO_STR[4] == "low"


# ---------------------------------------------------------------------------
# State/status mapping (unit tests)
# ---------------------------------------------------------------------------


def test_state_to_status():
    from modules.tasks.models import state_to_status

    assert state_to_status("in_progress") == "in-progress"
    assert state_to_status("backlog") == "backlog"
    assert state_to_status("todo") == "todo"
    assert state_to_status("done") == "done"
    assert state_to_status("blocked") == "blocked"


def test_status_to_state():
    from modules.tasks.models import status_to_state

    assert status_to_state("in-progress") == "in_progress"
    assert status_to_state("backlog") == "backlog"
    assert status_to_state("todo") == "todo"
    assert status_to_state("done") == "done"


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def test_create_task_with_dependencies():
    from modules.tasks.models import Task

    created = Task(
        id="101",
        title="Dependent Task",
        status="backlog",
        priority="medium",
        project=None,
        tags=[],
        blockedBy=["42"],
        blocks=[],
        createdAt="2026-02-18T00:00:00+00:00",
        updatedAt="2026-02-18T00:00:00+00:00",
    )
    with (
        patch("modules.tasks.service.create_task", new_callable=AsyncMock) as mock_create,
        patch("modules.activity.service.activity_service.log_event", new_callable=AsyncMock),
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock_create.return_value = created
        response = client.post("/api/tasks/", json={"title": "Dependent Task", "blockedBy": ["42"]})
        assert response.status_code == 200
        data = response.json()
        assert data["blockedBy"] == ["42"]


# ---------------------------------------------------------------------------
# Get single task
# ---------------------------------------------------------------------------


def test_get_task():
    from modules.tasks.models import Task

    task = Task(
        id="42",
        title="My Task",
        status="todo",
        priority="high",
        project="mc",
        tags=["infra"],
        createdAt="2026-02-01T00:00:00+00:00",
        updatedAt="2026-02-01T00:00:00+00:00",
    )
    with patch("modules.tasks.service.get_task", new_callable=AsyncMock) as mock:
        mock.return_value = task
        response = client.get("/api/tasks/42")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "42"
        assert data["title"] == "My Task"


def test_get_task_not_found():
    with patch("modules.tasks.service.get_task", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.get("/api/tasks/999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Run task
# ---------------------------------------------------------------------------


def test_run_task():
    from modules.tasks.models import Task

    task = Task(
        id="42",
        title="Running Task",
        status="in-progress",
        priority="medium",
        project=None,
        tags=[],
        createdAt="2026-02-01T00:00:00+00:00",
        updatedAt="2026-02-18T00:00:00+00:00",
    )
    with (
        patch("modules.tasks.service.run_task", new_callable=AsyncMock) as mock,
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock.return_value = task
        response = client.post("/api/tasks/42/run")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["message"] == "Task queued for execution"


def test_run_task_not_found():
    with (
        patch("modules.tasks.service.run_task", new_callable=AsyncMock) as mock,
        patch("core.websocket.manager.broadcast", new_callable=AsyncMock),
    ):
        mock.return_value = None
        response = client.post("/api/tasks/999/run")
        assert response.status_code == 404
