"""Integration tests for the Calendar module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_calendar():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "calendar" in ids


def test_get_calendar_empty():
    with (
        patch("modules.calendar.service.CalendarService.get_cron_jobs", new_callable=AsyncMock) as mock_cron,
        patch("modules.calendar.service.CalendarService.get_upcoming_tasks", new_callable=AsyncMock) as mock_tasks,
    ):
        mock_cron.return_value = []
        mock_tasks.return_value = []
        response = client.get("/api/calendar/")
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["cronJobs"] == []


def test_get_calendar_with_task_events():
    from modules.calendar.models import CalendarEvent

    events = [
        CalendarEvent(
            id="task-abc1",
            title="Review PR",
            description="Review the PR for the new feature",
            start=datetime.now(timezone.utc) + timedelta(hours=2),
            type="task",
            status="scheduled",
            agent=None,
        ),
    ]
    with (
        patch("modules.calendar.service.CalendarService.get_cron_jobs", new_callable=AsyncMock) as mock_cron,
        patch("modules.calendar.service.CalendarService.get_upcoming_tasks", new_callable=AsyncMock) as mock_tasks,
    ):
        mock_cron.return_value = []
        mock_tasks.return_value = events
        response = client.get("/api/calendar/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "Review PR"
        assert data["events"][0]["type"] == "task"


def test_get_calendar_with_cron_events():
    from modules.calendar.models import CalendarEvent, CronJob, CronPayload, CronSchedule

    cron_job = CronJob(
        jobId="cron-1",
        name="Daily report",
        schedule=CronSchedule(kind="every", everyMs=86400000),
        payload=CronPayload(kind="systemEvent", text="Generate daily report"),
        sessionTarget="main",
        enabled=True,
        nextRunAt=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    cron_event = CalendarEvent(
        id="cron-1",
        title="Daily report",
        start=datetime.now(timezone.utc) + timedelta(hours=1),
        type="cron",
        status="scheduled",
        agent="main",
    )
    with (
        patch("modules.calendar.service.CalendarService.get_cron_jobs", new_callable=AsyncMock) as mock_cron,
        patch("modules.calendar.service.CalendarService._cron_to_calendar_events") as mock_convert,
        patch("modules.calendar.service.CalendarService.get_upcoming_tasks", new_callable=AsyncMock) as mock_tasks,
    ):
        mock_cron.return_value = [cron_job]
        mock_convert.return_value = [cron_event]
        mock_tasks.return_value = []
        response = client.get("/api/calendar/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["type"] == "cron"
        assert len(data["cronJobs"]) == 1


def test_get_calendar_query_params():
    from modules.calendar.models import CalendarResponse

    with patch("modules.calendar.service.CalendarService.get_calendar", new_callable=AsyncMock) as mock_cal:
        mock_cal.return_value = CalendarResponse(events=[], cronJobs=[])
        response = client.get("/api/calendar/?days_ahead=7")
        assert response.status_code == 200
        mock_cal.assert_called_once()
        # get_calendar is called with (start_date, days_ahead) positional args
        call_args, call_kwargs = mock_cal.call_args
        days_ahead = call_kwargs.get("days_ahead") or (call_args[1] if len(call_args) > 1 else None)
        assert days_ahead == 7


def test_get_cron_jobs_empty():
    with patch("modules.calendar.service.CalendarService.get_cron_jobs", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/calendar/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["jobs"] == []
        assert data["total"] == 0


def test_get_cron_jobs_with_data():
    from modules.calendar.models import CronJob, CronPayload, CronSchedule

    jobs = [
        CronJob(
            jobId="cron-1",
            name="Morning check",
            schedule=CronSchedule(kind="cron", expr="0 8 * * *"),
            payload=CronPayload(kind="systemEvent", text="Morning check"),
            sessionTarget="main",
            enabled=True,
            runCount=42,
        ),
    ]
    with patch("modules.calendar.service.CalendarService.get_cron_jobs", new_callable=AsyncMock) as mock:
        mock.return_value = jobs
        response = client.get("/api/calendar/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["jobs"][0]["jobId"] == "cron-1"
        assert data["jobs"][0]["name"] == "Morning check"
        assert data["jobs"][0]["runCount"] == 42
