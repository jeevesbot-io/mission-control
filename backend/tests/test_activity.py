"""Integration tests for the Activity Timeline module."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_activity():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "activity" in ids


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------

def test_feed_empty():
    with patch("modules.activity.service.ActivityService.get_feed", new_callable=AsyncMock) as mock:
        from modules.activity.models import ActivityFeedResponse
        mock.return_value = ActivityFeedResponse(events=[], total=0, cursor=None)
        response = client.get("/api/activity/feed")
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0


def test_feed_returns_events():
    with patch("modules.activity.service.ActivityService.get_feed", new_callable=AsyncMock) as mock:
        from modules.activity.models import ActivityEvent, ActivityFeedResponse
        events = [
            ActivityEvent(
                id="evt-1",
                timestamp="2026-02-19T10:00:00+00:00",
                actor="user",
                action="task.created",
                resource_type="task",
                resource_id="task-1",
                resource_name="Build feature",
                module="warroom",
            ),
            ActivityEvent(
                id="evt-2",
                timestamp="2026-02-19T09:00:00+00:00",
                actor="user",
                action="agent.triggered",
                resource_type="agent",
                resource_id="research",
                resource_name="research",
                module="agents",
            ),
        ]
        mock.return_value = ActivityFeedResponse(events=events, total=2, cursor="2026-02-19T09:00:00+00:00")
        response = client.get("/api/activity/feed")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 2
        assert data["events"][0]["action"] == "task.created"
        assert data["events"][1]["module"] == "agents"
        assert data["cursor"] is not None


def test_feed_accepts_filters():
    with patch("modules.activity.service.ActivityService.get_feed", new_callable=AsyncMock) as mock:
        from modules.activity.models import ActivityFeedResponse
        mock.return_value = ActivityFeedResponse(events=[], total=0, cursor=None)
        response = client.get("/api/activity/feed?module=warroom&actor=user&limit=10")
        assert response.status_code == 200
        mock.assert_called_once_with(limit=10, cursor=None, module="warroom", actor="user", action=None)


def test_feed_pagination_with_cursor():
    with patch("modules.activity.service.ActivityService.get_feed", new_callable=AsyncMock) as mock:
        from modules.activity.models import ActivityFeedResponse
        mock.return_value = ActivityFeedResponse(events=[], total=0, cursor=None)
        response = client.get("/api/activity/feed?cursor=2026-02-19T10:00:00")
        assert response.status_code == 200
        mock.assert_called_once_with(limit=50, cursor="2026-02-19T10:00:00", module=None, actor=None, action=None)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_stats():
    with patch("modules.activity.service.ActivityService.get_stats", new_callable=AsyncMock) as mock:
        from modules.activity.models import ActivityStats
        mock.return_value = ActivityStats(
            total_events=42,
            by_module={"warroom": 20, "agents": 15, "content": 7},
            by_action={"task.created": 10, "agent.triggered": 15},
            last_24h=12,
        )
        response = client.get("/api/activity/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 42
        assert data["by_module"]["warroom"] == 20
        assert data["last_24h"] == 12


# ---------------------------------------------------------------------------
# Service unit tests (log_event)
# ---------------------------------------------------------------------------

def test_log_event():
    """Test that log_event creates an event and returns it."""
    from modules.activity.models import ActivityLogRequest
    from modules.activity.service import ActivityService

    service = ActivityService()

    with patch.object(service, "_append_sync") as mock_append, \
         patch("modules.activity.service.manager") as mock_manager:
        mock_manager.broadcast = AsyncMock()

        req = ActivityLogRequest(
            actor="user",
            action="task.created",
            resource_type="task",
            resource_id="t1",
            resource_name="Test Task",
            module="warroom",
        )

        import asyncio
        loop = asyncio.new_event_loop()
        try:
            event = loop.run_until_complete(service.log_event(req))
        finally:
            loop.close()

        assert event.actor == "user"
        assert event.action == "task.created"
        assert event.resource_name == "Test Task"
        assert event.module == "warroom"
        assert event.id  # UUID is set
        mock_append.assert_called_once()
        mock_manager.broadcast.assert_called_once()
