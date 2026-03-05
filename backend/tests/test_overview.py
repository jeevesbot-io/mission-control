"""Integration tests for the Overview module."""

import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app
from modules.overview.models import (
    AgentActivityItem,
    AgentStatusSummary,
    OverviewResponse,
    OverviewStats,
    RecentActivity,
    StandupResponse,
    SystemHealth,
    TaskQueueItem,
    UpcomingEvent,
)

client = TestClient(app)


def _mock_overview(**overrides) -> OverviewResponse:
    """Build a mock OverviewResponse with sensible defaults."""
    defaults = dict(
        stats=OverviewStats(
            agents_active=1,
            events_this_week=5,
            emails_processed=17,
            tasks_pending=3,
        ),
        agent_summary=AgentStatusSummary(
            total_entries=61,
            info_count=57,
            warning_count=3,
            entries_24h=12,
            unique_agents=1,
            health_rate=93.4,
        ),
        upcoming_events=[
            UpcomingEvent(
                id=1,
                child="Natty",
                summary="World Book Day",
                event_date="2026-03-03",
                event_end_date=None,
                event_time=None,
                days_away=3,
            ),
            UpcomingEvent(
                id=2,
                child="Elodie",
                summary="Sports Day",
                event_date="2026-03-05",
                event_end_date=None,
                event_time="14:00:00",
                days_away=5,
            ),
        ],
        recent_activity=[
            RecentActivity(
                id="1",
                agent_id="matron",
                level="info",
                message="Urgent check: No unread emails",
                created_at=datetime.datetime(2026, 2, 13, 8, 0, tzinfo=datetime.UTC),
            ),
        ],
        health=SystemHealth(
            status="healthy",
            database=True,
            uptime_seconds=3600.0,
            version="0.1.0",
        ),
    )
    defaults.update(overrides)
    return OverviewResponse(**defaults)


def test_modules_includes_overview():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "overview" in ids


def test_overview_returns_200():
    overview = _mock_overview()
    with patch(
        "modules.overview.service.OverviewService.get_overview",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = overview
        response = client.get("/api/overview/")
        assert response.status_code == 200


def test_overview_has_all_sections():
    overview = _mock_overview()
    with patch(
        "modules.overview.service.OverviewService.get_overview",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = overview
        response = client.get("/api/overview/")
        data = response.json()

        assert "stats" in data
        assert "agent_summary" in data
        assert "upcoming_events" in data
        assert "recent_activity" in data
        assert "health" in data


def test_overview_stats_shape():
    overview = _mock_overview()
    with patch(
        "modules.overview.service.OverviewService.get_overview",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = overview
        data = client.get("/api/overview/").json()
        stats = data["stats"]

        assert stats["agents_active"] == 1
        assert stats["events_this_week"] == 5
        assert stats["emails_processed"] == 17
        assert stats["tasks_pending"] == 3


def test_overview_upcoming_events():
    overview = _mock_overview()
    with patch(
        "modules.overview.service.OverviewService.get_overview",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = overview
        data = client.get("/api/overview/").json()
        events = data["upcoming_events"]

        assert len(events) == 2
        assert events[0]["child"] == "Natty"
        assert events[0]["summary"] == "World Book Day"
        assert events[0]["days_away"] == 3
        assert events[1]["child"] == "Elodie"
        assert events[1]["event_time"] == "14:00:00"


def test_overview_recent_activity():
    overview = _mock_overview()
    with patch(
        "modules.overview.service.OverviewService.get_overview",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = overview
        data = client.get("/api/overview/").json()
        activity = data["recent_activity"]

        assert len(activity) == 1
        assert activity[0]["agent_id"] == "matron"
        assert activity[0]["level"] == "info"
        assert activity[0]["message"] == "Urgent check: No unread emails"


def test_overview_health():
    overview = _mock_overview()
    with patch(
        "modules.overview.service.OverviewService.get_overview",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = overview
        data = client.get("/api/overview/").json()
        health = data["health"]

        assert health["status"] == "healthy"
        assert health["database"] is True
        assert health["version"] == "0.1.0"


def test_overview_empty_state():
    """Overview should work fine with no data."""
    overview = _mock_overview(
        stats=OverviewStats(
            agents_active=0,
            events_this_week=0,
            emails_processed=0,
            tasks_pending=0,
        ),
        agent_summary=AgentStatusSummary(
            total_entries=0,
            info_count=0,
            warning_count=0,
            entries_24h=0,
            unique_agents=0,
            health_rate=100.0,
        ),
        upcoming_events=[],
        recent_activity=[],
    )
    with patch(
        "modules.overview.service.OverviewService.get_overview",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = overview
        response = client.get("/api/overview/")
        assert response.status_code == 200
        data = response.json()
        assert data["upcoming_events"] == []
        assert data["recent_activity"] == []
        assert data["stats"]["agents_active"] == 0


def test_overview_agent_summary_fields():
    overview = _mock_overview()
    with patch(
        "modules.overview.service.OverviewService.get_overview",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = overview
        data = client.get("/api/overview/").json()
        summary = data["agent_summary"]

        assert summary["total_entries"] == 61
        assert summary["info_count"] == 57
        assert summary["warning_count"] == 3
        assert summary["entries_24h"] == 12
        assert summary["unique_agents"] == 1
        assert summary["health_rate"] == 93.4


def _mock_standup(**overrides) -> StandupResponse:
    """Build a mock StandupResponse with sensible defaults."""
    defaults = dict(
        date="2026-03-03",
        task_queue=[
            TaskQueueItem(
                id=1,
                title="Fix auth bug",
                state="todo",
                agent_id="builder",
                priority=2,
                labels=["bug"],
            ),
            TaskQueueItem(
                id=2,
                title="Write docs",
                state="in_progress",
                agent_id="scribe",
                priority=3,
                labels=["docs"],
            ),
        ],
        tasks_done_24h=3,
        tasks_in_progress=2,
        tasks_in_review=1,
        recent_agent_activity=[
            AgentActivityItem(
                agent_id="scribe",
                action="state_changed",
                detail="in_progress -> peer_review",
                created_at=datetime.datetime(2026, 3, 3, 10, 0, tzinfo=datetime.UTC),
            ),
        ],
        upcoming_events=[
            UpcomingEvent(
                id=1,
                child="Family",
                summary="Team meeting",
                event_date="2026-03-03",
                event_end_date=None,
                event_time="09:00",
                days_away=0,
            ),
        ],
        blockers=[],
    )
    defaults.update(overrides)
    return StandupResponse(**defaults)


def test_standup_returns_200():
    standup = _mock_standup()
    with patch(
        "modules.overview.service.OverviewService.get_standup",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = standup
        response = client.get("/api/overview/standup")
        assert response.status_code == 200


def test_standup_has_all_sections():
    standup = _mock_standup()
    with patch(
        "modules.overview.service.OverviewService.get_standup",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = standup
        data = client.get("/api/overview/standup").json()
        assert "date" in data
        assert "task_queue" in data
        assert "tasks_done_24h" in data
        assert "tasks_in_progress" in data
        assert "tasks_in_review" in data
        assert "recent_agent_activity" in data
        assert "upcoming_events" in data
        assert "blockers" in data


def test_standup_task_queue():
    standup = _mock_standup()
    with patch(
        "modules.overview.service.OverviewService.get_standup",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = standup
        data = client.get("/api/overview/standup").json()
        assert len(data["task_queue"]) == 2
        assert data["task_queue"][0]["title"] == "Fix auth bug"
        assert data["tasks_done_24h"] == 3
        assert data["tasks_in_progress"] == 2
        assert data["tasks_in_review"] == 1


def test_standup_empty_state():
    standup = _mock_standup(
        task_queue=[],
        tasks_done_24h=0,
        tasks_in_progress=0,
        tasks_in_review=0,
        recent_agent_activity=[],
        upcoming_events=[],
        blockers=[],
    )
    with patch(
        "modules.overview.service.OverviewService.get_standup",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = standup
        response = client.get("/api/overview/standup")
        assert response.status_code == 200
        data = response.json()
        assert data["task_queue"] == []
        assert data["blockers"] == []
