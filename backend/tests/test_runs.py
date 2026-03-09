"""Tests for the Agent Runs module."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from main import app
from modules.runs.models import AgentRun, AgentRunList

client = TestClient(app)

_SAMPLE_RUN = AgentRun(
    id=uuid4(),
    agent_id="dev-impl",
    run_type="task",
    trigger="manual",
    status="completed",
    summary="Built the thing",
    duration_ms=12000,
    tokens_used=5000,
    metadata={"task_id": "abc123"},
    prompt_preview="Build the logging module...",
    channel="slack",
    session_key="agent:dev-impl:abc",
    completed_at=datetime.now(timezone.utc),
    outcome="success",
    created_at=datetime.now(timezone.utc),
)

_TOKEN = "mc-trigger-2026"


# ---------------------------------------------------------------------------
# Module discovery
# ---------------------------------------------------------------------------


def test_modules_includes_runs():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "runs" in ids


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------


def test_ingest_creates_run():
    with patch("modules.runs.service.RunsService.ingest", new_callable=AsyncMock) as mock_ingest:
        mock_ingest.return_value = _SAMPLE_RUN
        response = client.post(
            "/api/runs/ingest",
            json={
                "agent_id": "dev-impl",
                "run_type": "task",
                "trigger": "manual",
                "status": "completed",
                "summary": "Built the thing",
                "duration_ms": 12000,
                "tokens_used": 5000,
                "outcome": "success",
                "channel": "slack",
            },
            headers={"X-MC-Token": _TOKEN},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == "dev-impl"
        assert data["outcome"] == "success"
        mock_ingest.assert_called_once()


def test_ingest_rejects_bad_token():
    response = client.post(
        "/api/runs/ingest",
        json={"agent_id": "test", "run_type": "task", "trigger": "manual", "status": "completed"},
        headers={"X-MC-Token": "wrong-token"},
    )
    assert response.status_code == 403


def test_ingest_rejects_missing_token():
    response = client.post(
        "/api/runs/ingest",
        json={"agent_id": "test", "run_type": "task", "trigger": "manual", "status": "completed"},
    )
    assert response.status_code == 422  # Missing required header


# ---------------------------------------------------------------------------
# List with filters
# ---------------------------------------------------------------------------


def test_list_runs():
    with patch("modules.runs.service.RunsService.list_runs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = AgentRunList(items=[_SAMPLE_RUN], total=1, page=1, page_size=50)
        response = client.get("/api/runs/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1


def test_list_runs_with_filters():
    with patch("modules.runs.service.RunsService.list_runs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = AgentRunList(items=[], total=0, page=1, page_size=50)
        response = client.get("/api/runs/?agent_id=dev-impl&outcome=success&date_from=2026-03-01")
        assert response.status_code == 200
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["agent_id"] == "dev-impl"
        assert call_kwargs["outcome"] == "success"
        assert call_kwargs["date_from"] == "2026-03-01"


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------


def test_get_run_not_found():
    with patch("modules.runs.service.RunsService.get_run", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = client.get(f"/api/runs/{uuid4()}")
        assert response.status_code == 404


def test_get_run_found():
    with patch("modules.runs.service.RunsService.get_run", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _SAMPLE_RUN
        response = client.get(f"/api/runs/{_SAMPLE_RUN.id}")
        assert response.status_code == 200
        assert response.json()["agent_id"] == "dev-impl"


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------


def test_heatmap():
    with patch("modules.runs.service.RunsService.get_heatmap", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/runs/heatmap?year=2026")
        assert response.status_code == 200
        assert response.json() == []
