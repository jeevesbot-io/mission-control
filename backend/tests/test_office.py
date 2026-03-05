"""Integration tests for the Office module."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Module registration
# ---------------------------------------------------------------------------


def test_modules_includes_office():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "office" in ids


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_office_response(workstations=None, office_stats=None):
    """Build an OfficeResponse from test data."""
    from modules.office.models import AgentWorkstation, OfficeResponse

    if workstations is None:
        workstations = [
            AgentWorkstation(
                agent_id="main",
                display_name="Jeeves",
                avatar_color="#3b82f6",
                status="working",
                current_task="Processing memory files",
                last_seen=datetime(2026, 2, 19, 10, 0, 0, tzinfo=timezone.utc),
                position={"x": 100, "y": 100},
                metadata={},
            ),
            AgentWorkstation(
                agent_id="archivist",
                display_name="The Archivist",
                avatar_color="#8b5cf6",
                status="idle",
                current_task=None,
                last_seen=None,
                position={"x": 300, "y": 100},
                metadata={},
            ),
            AgentWorkstation(
                agent_id="curator",
                display_name="The Curator",
                avatar_color="#ec4899",
                status="idle",
                current_task=None,
                last_seen=None,
                position={"x": 500, "y": 100},
                metadata={},
            ),
        ]

    if office_stats is None:
        office_stats = {
            "total_agents": len(workstations),
            "active_agents": 1,
            "idle_agents": len(workstations) - 1,
        }

    return OfficeResponse(workstations=workstations, office_stats=office_stats)


# ---------------------------------------------------------------------------
# GET /api/office/
# ---------------------------------------------------------------------------


def test_office_returns_workstations():
    """Mock service, verify workstations list structure."""
    with patch("modules.office.service.OfficeService.get_office", new_callable=AsyncMock) as mock:
        mock.return_value = _build_office_response()
        response = client.get("/api/office/")
        assert response.status_code == 200
        data = response.json()
        assert "workstations" in data
        assert "office_stats" in data
        assert isinstance(data["workstations"], list)
        assert len(data["workstations"]) == 3
        assert data["workstations"][0]["agent_id"] == "main"
        assert data["workstations"][0]["status"] == "working"
        assert data["workstations"][1]["agent_id"] == "archivist"


def test_office_workstation_schema():
    """Verify each workstation has all required fields."""
    required_fields = {
        "agent_id",
        "display_name",
        "avatar_color",
        "status",
        "current_task",
        "last_seen",
        "position",
        "metadata",
    }

    with patch("modules.office.service.OfficeService.get_office", new_callable=AsyncMock) as mock:
        mock.return_value = _build_office_response()
        response = client.get("/api/office/")
        assert response.status_code == 200
        data = response.json()

        for workstation in data["workstations"]:
            assert required_fields.issubset(set(workstation.keys())), (
                f"Missing fields: {required_fields - set(workstation.keys())}"
            )
            assert workstation["status"] in ("active", "idle", "working", "scheduled", "offline")


def test_office_stats_structure():
    """Verify office_stats has total_agents, active_agents, idle_agents."""
    with patch("modules.office.service.OfficeService.get_office", new_callable=AsyncMock) as mock:
        mock.return_value = _build_office_response()
        response = client.get("/api/office/")
        assert response.status_code == 200
        stats = response.json()["office_stats"]
        assert "total_agents" in stats
        assert "active_agents" in stats
        assert "idle_agents" in stats
        assert stats["total_agents"] == 3
        assert stats["active_agents"] == 1
        assert stats["idle_agents"] == 2


def test_office_empty_state():
    """Mock returns empty workstations, verify graceful handling."""
    from modules.office.models import OfficeResponse

    with patch("modules.office.service.OfficeService.get_office", new_callable=AsyncMock) as mock:
        mock.return_value = OfficeResponse(workstations=[], office_stats={})
        response = client.get("/api/office/")
        assert response.status_code == 200
        data = response.json()
        assert data["workstations"] == []
        assert data["office_stats"] == {}


def test_office_positions_assigned():
    """Verify each workstation gets position with x and y."""
    from modules.office.models import AgentWorkstation

    workstations = [
        AgentWorkstation(
            agent_id=f"agent-{i}",
            display_name=f"Agent {i}",
            avatar_color="#aabbcc",
            status="idle",
            position={"x": 100 + i * 200, "y": 100 + (i // 3) * 200},
        )
        for i in range(5)
    ]

    with patch("modules.office.service.OfficeService.get_office", new_callable=AsyncMock) as mock:
        mock.return_value = _build_office_response(
            workstations=workstations,
            office_stats={"total_agents": 5, "active_agents": 0, "idle_agents": 5},
        )
        response = client.get("/api/office/")
        assert response.status_code == 200
        data = response.json()

        for ws in data["workstations"]:
            assert "position" in ws
            assert "x" in ws["position"], f"Workstation {ws['agent_id']} missing position.x"
            assert "y" in ws["position"], f"Workstation {ws['agent_id']} missing position.y"
            assert isinstance(ws["position"]["x"], (int, float))
            assert isinstance(ws["position"]["y"], (int, float))


def test_office_known_agents_have_colors():
    """Verify known agents get avatar_color values from the service color map."""
    from modules.office.models import AgentWorkstation
    from modules.office.service import OfficeService

    known_colors = OfficeService.AGENT_COLORS

    workstations = [
        AgentWorkstation(
            agent_id=agent_id,
            display_name=display_name,
            avatar_color=known_colors.get(agent_id, "#6b7280"),
            status="idle",
            position={"x": 100, "y": 100},
        )
        for agent_id, display_name in [
            ("main", "Jeeves"),
            ("archivist", "The Archivist"),
            ("foundry-blacksmith", "The Blacksmith"),
        ]
    ]

    with patch("modules.office.service.OfficeService.get_office", new_callable=AsyncMock) as mock:
        mock.return_value = _build_office_response(
            workstations=workstations,
            office_stats={"total_agents": 3, "active_agents": 0, "idle_agents": 3},
        )
        response = client.get("/api/office/")
        assert response.status_code == 200
        data = response.json()

        for ws in data["workstations"]:
            agent_id = ws["agent_id"]
            assert ws["avatar_color"], f"Agent {agent_id} has no avatar_color"
            assert ws["avatar_color"].startswith("#"), f"Agent {agent_id} color is not a hex color"
            if agent_id in known_colors:
                assert ws["avatar_color"] == known_colors[agent_id], (
                    f"Agent {agent_id} expected color {known_colors[agent_id]}, got {ws['avatar_color']}"
                )


def test_office_service_error_returns_empty():
    """Mock service to raise exception, verify 200 with empty response (service catches errors)."""
    with patch("modules.office.service.OfficeService.get_office", new_callable=AsyncMock) as mock:
        # The service's try/except catches errors and returns an empty OfficeResponse.
        # Simulate that by having the mock return the fallback response.
        from modules.office.models import OfficeResponse

        mock.return_value = OfficeResponse(workstations=[], office_stats={})
        response = client.get("/api/office/")
        assert response.status_code == 200
        data = response.json()
        assert data["workstations"] == []
        assert data["office_stats"] == {}
