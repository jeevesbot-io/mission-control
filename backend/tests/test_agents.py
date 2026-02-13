"""Integration tests for the Agents module."""

import datetime
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from main import app

client = TestClient(app)


def test_modules_includes_agents():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "agents" in ids


def test_list_agents_empty():
    """When no agent_runs exist, list should return empty."""
    with patch("modules.agents.service.AgentService.list_agents", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/agents/")
        assert response.status_code == 200
        assert response.json() == []


def test_list_agents_with_data():
    """Should return agent info when runs exist."""
    from modules.agents.models import AgentInfo

    agents = [
        AgentInfo(
            agent_id="test-agent",
            last_run=datetime.datetime(2026, 1, 15, 10, 0, tzinfo=datetime.UTC),
            last_status="success",
            total_runs=5,
        )
    ]
    with patch("modules.agents.service.AgentService.list_agents", new_callable=AsyncMock) as mock:
        mock.return_value = agents
        response = client.get("/api/agents/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_id"] == "test-agent"
        assert data[0]["total_runs"] == 5
        assert data[0]["last_status"] == "success"


def test_get_stats():
    """Should return aggregate stats."""
    from modules.agents.models import AgentStatsResponse

    stats = AgentStatsResponse(
        total_runs=100, success_rate=95.0, runs_24h=12, unique_agents=3
    )
    with patch("modules.agents.service.AgentService.get_stats", new_callable=AsyncMock) as mock:
        mock.return_value = stats
        response = client.get("/api/agents/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_runs"] == 100
        assert data["success_rate"] == 95.0
        assert data["runs_24h"] == 12
        assert data["unique_agents"] == 3


def test_get_stats_empty():
    """Should return zeros when no runs exist."""
    from modules.agents.models import AgentStatsResponse

    stats = AgentStatsResponse(
        total_runs=0, success_rate=0.0, runs_24h=0, unique_agents=0
    )
    with patch("modules.agents.service.AgentService.get_stats", new_callable=AsyncMock) as mock:
        mock.return_value = stats
        response = client.get("/api/agents/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_runs"] == 0


def test_get_agent_runs():
    """Should return paginated run history."""
    from modules.agents.models import AgentRunResponse

    runs = [
        AgentRunResponse(
            id=str(uuid.uuid4()),
            agent_id="test-agent",
            run_type="scheduled",
            trigger="cron",
            status="success",
            summary="Completed successfully",
            duration_ms=1500,
            tokens_used=100,
            created_at=datetime.datetime(2026, 1, 15, 10, 0, tzinfo=datetime.UTC),
        )
    ]
    with patch("modules.agents.service.AgentService.get_runs", new_callable=AsyncMock) as mock:
        mock.return_value = (runs, 1)
        response = client.get("/api/agents/test-agent/runs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["runs"]) == 1
        assert data["runs"][0]["agent_id"] == "test-agent"
        assert data["runs"][0]["status"] == "success"


def test_get_agent_runs_with_filters():
    """Should pass filters through to service."""
    with patch("modules.agents.service.AgentService.get_runs", new_callable=AsyncMock) as mock:
        mock.return_value = ([], 0)
        response = client.get("/api/agents/test-agent/runs?status=error&page=2&page_size=10")
        assert response.status_code == 200
        mock.assert_called_once()
        call_kwargs = mock.call_args
        # Verify filters were passed
        assert call_kwargs.kwargs.get("status") == "error" or call_kwargs[1].get("status") == "error"


def test_get_agent_runs_pagination_validation():
    """Page must be >= 1."""
    response = client.get("/api/agents/test-agent/runs?page=0")
    assert response.status_code == 422


def test_trigger_agent_success():
    """Should trigger agent via gateway."""
    with patch(
        "modules.agents.service.AgentService.trigger_agent", new_callable=AsyncMock
    ) as mock:
        mock.return_value = (True, "Agent triggered successfully")
        response = client.post("/api/agents/test-agent/trigger")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "test-agent"


def test_trigger_agent_failure():
    """Should return 502 when gateway fails."""
    with patch(
        "modules.agents.service.AgentService.trigger_agent", new_callable=AsyncMock
    ) as mock:
        mock.return_value = (False, "Gateway unreachable")
        response = client.post("/api/agents/test-agent/trigger")
        assert response.status_code == 502


def test_get_cron():
    """Should return cron schedule."""
    from modules.agents.models import CronJob

    jobs = [
        CronJob(
            agent_id="daily-report",
            schedule="0 8 * * *",
            enabled=True,
            last_run="2026-01-15T08:00:00Z",
            next_run="2026-01-16T08:00:00Z",
        )
    ]
    with patch(
        "modules.agents.service.AgentService.get_cron_jobs", new_callable=AsyncMock
    ) as mock:
        mock.return_value = jobs
        response = client.get("/api/agents/cron")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["agent_id"] == "daily-report"
        assert data["jobs"][0]["schedule"] == "0 8 * * *"


def test_get_cron_empty():
    """Should return empty when gateway is down."""
    with patch(
        "modules.agents.service.AgentService.get_cron_jobs", new_callable=AsyncMock
    ) as mock:
        mock.return_value = []
        response = client.get("/api/agents/cron")
        assert response.status_code == 200
        assert response.json()["jobs"] == []
