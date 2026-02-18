"""Office module business logic."""

from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AgentWorkstation, OfficeResponse


class OfficeService:
    """Service for office view operations."""

    AGENT_COLORS = {
        "main": "#3b82f6",
        "matron": "#f97316",
        "archivist": "#8b5cf6",
        "curator": "#ec4899",
        "foundry-blacksmith": "#14b8a6",
        "foundry-scout": "#06b6d4",
        "foundry-spec": "#10b981",
        "foundry-builder": "#84cc16",
    }

    AGENT_NAMES = {
        "main": "Jeeves",
        "matron": "Matron",
        "archivist": "The Archivist",
        "curator": "The Curator",
        "foundry-blacksmith": "The Blacksmith",
        "foundry-scout": "Scout",
        "foundry-spec": "Spec Writer",
        "foundry-builder": "Builder",
    }

    POSITIONS = [
        {"x": 100, "y": 100},
        {"x": 300, "y": 100},
        {"x": 500, "y": 100},
        {"x": 100, "y": 300},
        {"x": 300, "y": 300},
        {"x": 500, "y": 300},
        {"x": 100, "y": 500},
        {"x": 300, "y": 500},
    ]

    async def get_office(self, db: AsyncSession) -> OfficeResponse:
        """Get office view with all agent workstations."""
        try:
            # Get recent agent activity from agent_log
            query = text(
                """
                SELECT agent, MAX(timestamp) as last_seen, message
                FROM agent_log
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                GROUP BY agent
                ORDER BY last_seen DESC
                """
            )
            result = await db.execute(query)
            rows = result.fetchall()

            workstations = []
            active_agents = {}

            for row in rows:
                agent_id = row.agent
                active_agents[agent_id] = {
                    "last_seen": row.last_seen,
                    "current_task": row.message[:100] if row.message else None,
                }

            # Create workstations for all known agents
            for idx, (agent_id, display_name) in enumerate(self.AGENT_NAMES.items()):
                if idx < len(self.POSITIONS):
                    position = self.POSITIONS[idx]
                else:
                    position = {"x": 100 + (idx % 3) * 200, "y": 100 + (idx // 3) * 200}

                status = "idle"
                current_task = None
                last_seen = None

                if agent_id in active_agents:
                    status = "working"
                    current_task = active_agents[agent_id]["current_task"]
                    last_seen = active_agents[agent_id]["last_seen"]

                workstation = AgentWorkstation(
                    agent_id=agent_id,
                    display_name=display_name,
                    avatar_color=self.AGENT_COLORS.get(agent_id, "#6b7280"),
                    status=status,
                    current_task=current_task,
                    last_seen=last_seen,
                    position=position,
                )
                workstations.append(workstation)

            office_stats = {
                "total_agents": len(workstations),
                "active_agents": len(active_agents),
                "idle_agents": len(workstations) - len(active_agents),
            }

            return OfficeResponse(workstations=workstations, office_stats=office_stats)

        except Exception as e:
            print(f"Error getting office view: {e}")
            return OfficeResponse(workstations=[], office_stats={})


office_service = OfficeService()
