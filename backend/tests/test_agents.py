"""Integration tests for the Agents module."""

import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_agents():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "agents" in ids


def test_list_agents():
    """Should return agents from agent_log."""
    from modules.agents.models import AgentInfo

    agents = [
        AgentInfo(
            agent_id="matron",
            last_activity=datetime.datetime(2026, 2, 14, 9, 31, tzinfo=datetime.UTC),
            last_message="Urgent check: No unread emails",
            last_level="info",
            total_entries=61,
            warning_count=3,
        )
    ]
    with patch(
        "modules.agents.service.AgentService.list_agents", new_callable=AsyncMock
    ) as mock:
        mock.return_value = agents
        response = client.get("/api/agents/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_id"] == "matron"
        assert data[0]["total_entries"] == 61
        assert data[0]["warning_count"] == 3


def test_list_agents_empty():
    """Should handle no agents."""
    with patch(
        "modules.agents.service.AgentService.list_agents", new_callable=AsyncMock
    ) as mock:
        mock.return_value = []
        response = client.get("/api/agents/")
        assert response.status_code == 200
        assert response.json() == []


def test_get_stats():
    """Should return agent stats."""
    from modules.agents.models import AgentStatsResponse

    stats = AgentStatsResponse(
        total_entries=61,
        unique_agents=1,
        entries_24h=12,
        warning_count=3,
        health_rate=93.4,
    )
    with patch(
        "modules.agents.service.AgentService.get_stats", new_callable=AsyncMock
    ) as mock:
        mock.return_value = stats
        response = client.get("/api/agents/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_entries"] == 61
        assert data["health_rate"] == 93.4


def test_get_stats_empty():
    """Should handle zero stats."""
    from modules.agents.models import AgentStatsResponse

    stats = AgentStatsResponse(
        total_entries=0,
        unique_agents=0,
        entries_24h=0,
        warning_count=0,
        health_rate=100.0,
    )
    with patch(
        "modules.agents.service.AgentService.get_stats", new_callable=AsyncMock
    ) as mock:
        mock.return_value = stats
        response = client.get("/api/agents/stats")
        assert response.status_code == 200
        assert response.json()["total_entries"] == 0


def test_get_agent_log():
    """Should return paginated log for an agent."""
    from modules.agents.models import AgentLogEntry

    entries = [
        AgentLogEntry(
            id=61,
            agent_id="matron",
            level="info",
            message="Urgent check: No unread emails",
            metadata=None,
            created_at=datetime.datetime(2026, 2, 14, 9, 31, tzinfo=datetime.UTC),
        )
    ]
    with patch(
        "modules.agents.service.AgentService.get_log", new_callable=AsyncMock
    ) as mock:
        mock.return_value = (entries, 1)
        response = client.get("/api/agents/matron/log")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["message"] == "Urgent check: No unread emails"


def test_get_agent_log_empty():
    """Should handle no log entries."""
    with patch(
        "modules.agents.service.AgentService.get_log", new_callable=AsyncMock
    ) as mock:
        mock.return_value = ([], 0)
        response = client.get("/api/agents/matron/log")
        assert response.status_code == 200
        assert response.json()["entries"] == []


def test_trigger_agent_success():
    """Should trigger agent via gateway."""
    with patch(
        "modules.agents.service.AgentService.trigger_agent", new_callable=AsyncMock
    ) as mock:
        mock.return_value = (True, "Agent matron triggered successfully")
        response = client.post("/api/agents/matron/trigger")
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_trigger_agent_failure():
    """Should return 502 on gateway failure."""
    with patch(
        "modules.agents.service.AgentService.trigger_agent", new_callable=AsyncMock
    ) as mock:
        mock.return_value = (False, "Gateway returned 500")
        response = client.post("/api/agents/matron/trigger")
        assert response.status_code == 502
