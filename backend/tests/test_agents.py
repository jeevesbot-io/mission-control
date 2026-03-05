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
    with patch("modules.agents.service.AgentService.list_agents", new_callable=AsyncMock) as mock:
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
    with patch("modules.agents.service.AgentService.list_agents", new_callable=AsyncMock) as mock:
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
    with patch("modules.agents.service.AgentService.get_stats", new_callable=AsyncMock) as mock:
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
    with patch("modules.agents.service.AgentService.get_stats", new_callable=AsyncMock) as mock:
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
    with patch("modules.agents.service.AgentService.get_log", new_callable=AsyncMock) as mock:
        mock.return_value = (entries, 1)
        response = client.get("/api/agents/matron/log")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["message"] == "Urgent check: No unread emails"


def test_get_agent_log_empty():
    """Should handle no log entries."""
    with patch("modules.agents.service.AgentService.get_log", new_callable=AsyncMock) as mock:
        mock.return_value = ([], 0)
        response = client.get("/api/agents/matron/log")
        assert response.status_code == 200
        assert response.json()["entries"] == []


def test_trigger_agent_success():
    """Should trigger agent via gateway."""
    with patch("modules.agents.service.AgentService.trigger_agent", new_callable=AsyncMock) as mock:
        mock.return_value = (True, "Agent matron triggered successfully")
        response = client.post("/api/agents/matron/trigger")
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_trigger_agent_failure():
    """Should return 502 on gateway failure."""
    with patch("modules.agents.service.AgentService.trigger_agent", new_callable=AsyncMock) as mock:
        mock.return_value = (False, "Gateway returned 500")
        response = client.post("/api/agents/matron/trigger")
        assert response.status_code == 502


def test_list_agents_detailed():
    """Should return agents with rich metadata, status, and task counts."""
    from modules.agents.models import AgentDetailResponse

    detailed = [
        AgentDetailResponse(
            agent_id="main",
            display_name="Jeeves",
            role="Chief of Staff",
            model="claude-sonnet-4-6",
            tier="persistent",
            status="active",
            last_activity=datetime.datetime(2026, 3, 3, 12, 0, tzinfo=datetime.UTC),
            last_message="Daily briefing sent",
            last_level="info",
            total_entries=200,
            warning_count=5,
            tasks_in_progress=3,
            tasks_assigned=12,
            responsibilities=["Orchestration", "User interface"],
        ),
    ]
    with patch(
        "modules.agents.service.AgentService.list_agents_detailed",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = detailed
        response = client.get("/api/agents/detailed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_id"] == "main"
        assert data[0]["role"] == "Chief of Staff"
        assert data[0]["status"] == "active"
        assert data[0]["tasks_in_progress"] == 3
        assert data[0]["responsibilities"] == ["Orchestration", "User interface"]


# --- Office view tests (merged from Office module) ---


def test_agents_office_view_returns_workstations():
    """GET /api/agents/office returns 200 with a workstations key containing a list."""
    from modules.agents.models import OfficeViewResponse, AgentWorkstation

    response_data = OfficeViewResponse(
        workstations=[
            AgentWorkstation(
                agent_id="main",
                display_name="Jeeves",
                avatar_color="#3b82f6",
                status="idle",
                position={"x": 100, "y": 100},
            )
        ],
        office_stats={"total_agents": 1, "active_agents": 0, "idle_agents": 1},
    )
    with patch(
        "modules.agents.service.AgentService.get_office_view",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = response_data
        response = client.get("/api/agents/office")
        assert response.status_code == 200
        data = response.json()
        assert "workstations" in data
        assert isinstance(data["workstations"], list)


def test_agents_office_view_schema():
    """Each workstation dict has: agent_id, display_name, avatar_color, status, position."""
    from modules.agents.models import OfficeViewResponse, AgentWorkstation

    ws = AgentWorkstation(
        agent_id="matron",
        display_name="Matron",
        avatar_color="#f97316",
        status="working",
        position={"x": 300, "y": 100},
    )
    response_data = OfficeViewResponse(
        workstations=[ws],
        office_stats={"total_agents": 1, "active_agents": 1, "idle_agents": 0},
    )
    with patch(
        "modules.agents.service.AgentService.get_office_view",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = response_data
        response = client.get("/api/agents/office")
        assert response.status_code == 200
        station = response.json()["workstations"][0]
        for key in ("agent_id", "display_name", "avatar_color", "status", "position"):
            assert key in station, f"Missing key: {key}"


def test_agents_office_view_stats():
    """Response has office_stats key with total, active, idle counts."""
    from modules.agents.models import OfficeViewResponse

    response_data = OfficeViewResponse(
        workstations=[],
        office_stats={"total_agents": 8, "active_agents": 3, "idle_agents": 5},
    )
    with patch(
        "modules.agents.service.AgentService.get_office_view",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = response_data
        response = client.get("/api/agents/office")
        assert response.status_code == 200
        stats = response.json()["office_stats"]
        assert "total_agents" in stats
        assert "active_agents" in stats
        assert "idle_agents" in stats


def test_agents_office_view_empty():
    """When no recent agent_log entries, returns 200 with workstations (may show all as idle)."""
    from modules.agents.models import OfficeViewResponse, AgentWorkstation

    # All agents present but idle
    workstations = [
        AgentWorkstation(
            agent_id="main",
            display_name="Jeeves",
            avatar_color="#3b82f6",
            status="idle",
            position={"x": 100, "y": 100},
        ),
    ]
    response_data = OfficeViewResponse(
        workstations=workstations,
        office_stats={"total_agents": 1, "active_agents": 0, "idle_agents": 1},
    )
    with patch(
        "modules.agents.service.AgentService.get_office_view",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = response_data
        response = client.get("/api/agents/office")
        assert response.status_code == 200
        data = response.json()
        assert len(data["workstations"]) >= 1
        assert data["office_stats"]["active_agents"] == 0


def test_agents_office_active_from_recent_log():
    """Agents with recent activity get 'working' status."""
    from modules.agents.models import OfficeViewResponse, AgentWorkstation

    workstations = [
        AgentWorkstation(
            agent_id="matron",
            display_name="Matron",
            avatar_color="#f97316",
            status="working",
            current_task="Checking emails",
            last_seen=datetime.datetime(2026, 3, 5, 12, 0, tzinfo=datetime.UTC),
            position={"x": 300, "y": 100},
        ),
        AgentWorkstation(
            agent_id="main",
            display_name="Jeeves",
            avatar_color="#3b82f6",
            status="idle",
            position={"x": 100, "y": 100},
        ),
    ]
    response_data = OfficeViewResponse(
        workstations=workstations,
        office_stats={"total_agents": 2, "active_agents": 1, "idle_agents": 1},
    )
    with patch(
        "modules.agents.service.AgentService.get_office_view",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = response_data
        response = client.get("/api/agents/office")
        assert response.status_code == 200
        stations = response.json()["workstations"]
        working = [s for s in stations if s["status"] == "working"]
        assert len(working) == 1
        assert working[0]["agent_id"] == "matron"


def test_agents_office_known_agents_colors():
    """Each workstation has a non-empty avatar_color."""
    from modules.agents.models import OfficeViewResponse, AgentWorkstation

    workstations = [
        AgentWorkstation(
            agent_id=aid,
            display_name=name,
            avatar_color=color,
            status="idle",
            position={"x": 100, "y": 100},
        )
        for aid, name, color in [
            ("main", "Jeeves", "#3b82f6"),
            ("matron", "Matron", "#f97316"),
            ("archivist", "The Archivist", "#8b5cf6"),
        ]
    ]
    response_data = OfficeViewResponse(
        workstations=workstations,
        office_stats={"total_agents": 3, "active_agents": 0, "idle_agents": 3},
    )
    with patch(
        "modules.agents.service.AgentService.get_office_view",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = response_data
        response = client.get("/api/agents/office")
        assert response.status_code == 200
        for station in response.json()["workstations"]:
            assert station["avatar_color"], f"Empty avatar_color for {station['agent_id']}"
            assert len(station["avatar_color"]) > 0
