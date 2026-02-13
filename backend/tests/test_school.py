"""Integration tests for the School module."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_school():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "school" in ids


def test_list_events():
    """Should return school events."""
    from modules.school.models import SchoolEvent
    import datetime

    events = [
        SchoolEvent(
            id=1,
            title="Parent-Teacher Conference",
            description="Meet with teachers",
            start_time=datetime.datetime(2026, 2, 20, 14, 0, tzinfo=datetime.UTC),
            end_time=datetime.datetime(2026, 2, 20, 16, 0, tzinfo=datetime.UTC),
            location="Room 201",
            all_day=False,
        )
    ]
    with patch(
        "modules.school.service.SchoolService.get_events", new_callable=AsyncMock
    ) as mock:
        mock.return_value = events
        response = client.get("/api/school/events")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["events"][0]["title"] == "Parent-Teacher Conference"
        assert data["events"][0]["location"] == "Room 201"


def test_list_events_empty():
    """Should return empty list when no events."""
    with patch(
        "modules.school.service.SchoolService.get_events", new_callable=AsyncMock
    ) as mock:
        mock.return_value = []
        response = client.get("/api/school/events")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["events"] == []


def test_list_emails():
    """Should return school emails."""
    from modules.school.models import SchoolEmail
    import datetime

    emails = [
        SchoolEmail(
            id=1,
            subject="Field Trip Permission",
            sender="teacher@school.edu",
            preview="Please sign the attached permission slip...",
            received_at=datetime.datetime(2026, 2, 10, 9, 30, tzinfo=datetime.UTC),
            is_read=False,
        )
    ]
    with patch(
        "modules.school.service.SchoolService.get_emails", new_callable=AsyncMock
    ) as mock:
        mock.return_value = emails
        response = client.get("/api/school/emails")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["emails"][0]["subject"] == "Field Trip Permission"
        assert data["emails"][0]["is_read"] is False


def test_list_emails_empty():
    """Should handle no emails."""
    with patch(
        "modules.school.service.SchoolService.get_emails", new_callable=AsyncMock
    ) as mock:
        mock.return_value = []
        response = client.get("/api/school/emails")
        assert response.status_code == 200
        assert response.json()["emails"] == []


def test_list_tasks():
    """Should return todoist tasks."""
    from modules.school.models import TodoistTask

    tasks = [
        TodoistTask(
            id="task-1",
            content="Submit homework",
            description="Math worksheet",
            priority=3,
            due_date="2026-02-15",
            is_completed=False,
            project_name="School",
        )
    ]
    with patch(
        "modules.school.service.SchoolService.get_tasks", new_callable=AsyncMock
    ) as mock:
        mock.return_value = tasks
        response = client.get("/api/school/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["content"] == "Submit homework"
        assert data["tasks"][0]["priority"] == 3
        assert data["tasks"][0]["is_completed"] is False


def test_list_tasks_empty():
    """Should handle no tasks."""
    with patch(
        "modules.school.service.SchoolService.get_tasks", new_callable=AsyncMock
    ) as mock:
        mock.return_value = []
        response = client.get("/api/school/tasks")
        assert response.status_code == 200
        assert response.json()["tasks"] == []


def test_get_stats():
    """Should return school stats."""
    from modules.school.models import SchoolStatsResponse

    stats = SchoolStatsResponse(
        upcoming_events=3,
        unread_emails=5,
        pending_tasks=8,
        completed_today=2,
    )
    with patch(
        "modules.school.service.SchoolService.get_stats", new_callable=AsyncMock
    ) as mock:
        mock.return_value = stats
        response = client.get("/api/school/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["upcoming_events"] == 3
        assert data["unread_emails"] == 5
        assert data["pending_tasks"] == 8
        assert data["completed_today"] == 2


def test_get_stats_zeros():
    """Should handle all-zero stats."""
    from modules.school.models import SchoolStatsResponse

    stats = SchoolStatsResponse(
        upcoming_events=0, unread_emails=0, pending_tasks=0, completed_today=0
    )
    with patch(
        "modules.school.service.SchoolService.get_stats", new_callable=AsyncMock
    ) as mock:
        mock.return_value = stats
        response = client.get("/api/school/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["upcoming_events"] == 0


def test_events_limit_validation():
    """Limit must be between 1 and 200."""
    response = client.get("/api/school/events?limit=0")
    assert response.status_code == 422

    response = client.get("/api/school/events?limit=300")
    assert response.status_code == 422
