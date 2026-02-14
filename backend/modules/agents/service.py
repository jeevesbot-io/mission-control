"""Agents module service — queries agent_log table, triggers via OpenClaw gateway."""

import datetime
import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings

from .models import AgentInfo, AgentLogEntry, AgentStatsResponse, CronJob

logger = logging.getLogger(__name__)


class AgentService:
    """Query agent_log table and interact with OpenClaw gateway."""

    async def list_agents(self, db: AsyncSession) -> list[AgentInfo]:
        """List known agents with summary stats from agent_log."""
        try:
            result = await db.execute(
                text("""
                    SELECT
                        agent,
                        COUNT(*) as total_entries,
                        MAX(created_at) as last_activity,
                        COUNT(*) FILTER (WHERE level IN ('warning', 'WARNING', 'error', 'ERROR')) as warning_count
                    FROM agent_log
                    GROUP BY agent
                    ORDER BY last_activity DESC
                """)
            )
            agents = []
            for row in result.fetchall():
                # Get last message for status context
                last_msg_result = await db.execute(
                    text("""
                        SELECT message, level FROM agent_log
                        WHERE agent = :agent
                        ORDER BY created_at DESC LIMIT 1
                    """),
                    {"agent": row.agent},
                )
                last = last_msg_result.fetchone()

                agents.append(
                    AgentInfo(
                        agent_id=row.agent,
                        last_activity=row.last_activity,
                        last_message=last.message if last else None,
                        last_level=last.level.lower() if last else None,
                        total_entries=row.total_entries,
                        warning_count=row.warning_count,
                    )
                )
            return agents
        except Exception as exc:
            logger.warning("Failed to list agents: %s", exc)
            return []

    async def get_log(
        self,
        db: AsyncSession,
        agent_id: str | None = None,
        level: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentLogEntry], int]:
        """Paginated log history with optional filters."""
        try:
            filters = []
            params: dict = {}

            if agent_id:
                filters.append("agent = :agent_id")
                params["agent_id"] = agent_id

            if level:
                filters.append("LOWER(level) = :level")
                params["level"] = level.lower()

            where = f"WHERE {' AND '.join(filters)}" if filters else ""

            count_result = await db.execute(
                text(f"SELECT COUNT(*) FROM agent_log {where}"), params
            )
            total = count_result.scalar_one()

            offset = (page - 1) * page_size
            params["limit"] = page_size
            params["offset"] = offset

            result = await db.execute(
                text(f"""
                    SELECT id, agent, level, message, metadata, created_at
                    FROM agent_log
                    {where}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                params,
            )

            entries = [
                AgentLogEntry(
                    id=row.id,
                    agent_id=row.agent,
                    level=row.level.lower(),
                    message=row.message,
                    metadata=row.metadata,
                    created_at=row.created_at,
                )
                for row in result.fetchall()
            ]

            return entries, total
        except Exception as exc:
            logger.warning("Failed to get agent log: %s", exc)
            return [], 0

    async def get_stats(self, db: AsyncSession) -> AgentStatsResponse:
        """Aggregate stats from agent_log."""
        try:
            result = await db.execute(
                text("""
                    SELECT
                        COUNT(*) as total_entries,
                        COUNT(DISTINCT agent) as unique_agents,
                        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as entries_24h,
                        COUNT(*) FILTER (WHERE level IN ('warning', 'WARNING', 'error', 'ERROR')) as warning_count,
                        COUNT(*) FILTER (WHERE level IN ('info', 'INFO')) as info_count
                    FROM agent_log
                """)
            )
            row = result.fetchone()

            if not row or row.total_entries == 0:
                return AgentStatsResponse(
                    total_entries=0,
                    unique_agents=0,
                    entries_24h=0,
                    warning_count=0,
                    health_rate=100.0,
                )

            # Health rate = percentage of non-warning/error entries
            health_rate = round(row.info_count / row.total_entries * 100, 1)

            return AgentStatsResponse(
                total_entries=row.total_entries,
                unique_agents=row.unique_agents,
                entries_24h=row.entries_24h,
                warning_count=row.warning_count,
                health_rate=health_rate,
            )
        except Exception as exc:
            logger.warning("Failed to get agent stats: %s", exc)
            return AgentStatsResponse(
                total_entries=0,
                unique_agents=0,
                entries_24h=0,
                warning_count=0,
                health_rate=0.0,
            )

    async def trigger_agent(self, agent_id: str) -> tuple[bool, str]:
        """Trigger agent via OpenClaw gateway HTTP call."""
        url = f"{settings.openclaw_url}/api/agents/{agent_id}/trigger"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url)
                if resp.status_code < 300:
                    return True, f"Agent {agent_id} triggered successfully"
                return False, f"Gateway returned {resp.status_code}: {resp.text}"
        except httpx.RequestError as exc:
            logger.warning("Failed to trigger agent %s: %s", agent_id, exc)
            return False, f"Failed to reach gateway: {exc}"

    async def get_cron_jobs(self) -> list[CronJob]:
        """Fetch cron schedule from OpenClaw gateway."""
        url = f"{settings.openclaw_url}/api/cron"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return [CronJob(**job) for job in data.get("jobs", [])]
                return []
        except httpx.RequestError as exc:
            logger.warning("Failed to fetch cron jobs: %s", exc)
            return []


agent_service = AgentService()
