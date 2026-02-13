"""Agents module service — queries agent_runs, triggers via OpenClaw gateway."""

import datetime
import logging

import httpx
from sqlalchemy import Select, desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import AgentRun

from .models import AgentInfo, AgentRunResponse, AgentStatsResponse, CronJob

logger = logging.getLogger(__name__)


class AgentService:
    """Query agent_runs table and interact with OpenClaw gateway."""

    async def list_agents(self, db: AsyncSession) -> list[AgentInfo]:
        """List known agents with last run info."""
        # Subquery for last run per agent
        subq = (
            select(
                AgentRun.agent_id,
                func.count().label("total_runs"),
                func.max(AgentRun.created_at).label("last_run"),
            )
            .group_by(AgentRun.agent_id)
            .subquery()
        )

        result = await db.execute(
            select(subq.c.agent_id, subq.c.total_runs, subq.c.last_run)
            .order_by(desc(subq.c.last_run))
        )
        rows = result.all()

        agents: list[AgentInfo] = []
        for row in rows:
            # Get last status
            last_run_q = await db.execute(
                select(AgentRun.status)
                .where(AgentRun.agent_id == row.agent_id)
                .order_by(desc(AgentRun.created_at))
                .limit(1)
            )
            last_status = last_run_q.scalar_one_or_none()

            agents.append(
                AgentInfo(
                    agent_id=row.agent_id,
                    last_run=row.last_run,
                    last_status=last_status,
                    total_runs=row.total_runs,
                )
            )

        return agents

    async def get_runs(
        self,
        db: AsyncSession,
        agent_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentRunResponse], int]:
        """Paginated run history with optional filters."""
        query: Select = select(AgentRun).order_by(desc(AgentRun.created_at))
        count_query = select(func.count()).select_from(AgentRun)

        if agent_id:
            query = query.where(AgentRun.agent_id == agent_id)
            count_query = count_query.where(AgentRun.agent_id == agent_id)

        if status:
            query = query.where(AgentRun.status == status)
            count_query = count_query.where(AgentRun.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        runs = [
            AgentRunResponse(
                id=str(run.id),
                agent_id=run.agent_id,
                run_type=run.run_type,
                trigger=run.trigger,
                status=run.status,
                summary=run.summary,
                duration_ms=run.duration_ms,
                tokens_used=run.tokens_used,
                created_at=run.created_at,
            )
            for run in result.scalars().all()
        ]

        return runs, total

    async def get_stats(self, db: AsyncSession) -> AgentStatsResponse:
        """Aggregate stats: total runs, success rate, 24h count, unique agents."""
        total_result = await db.execute(select(func.count()).select_from(AgentRun))
        total_runs = total_result.scalar_one()

        if total_runs == 0:
            return AgentStatsResponse(
                total_runs=0, success_rate=0.0, runs_24h=0, unique_agents=0
            )

        success_result = await db.execute(
            select(func.count())
            .select_from(AgentRun)
            .where(AgentRun.status == "success")
        )
        success_count = success_result.scalar_one()

        cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=24)
        recent_result = await db.execute(
            select(func.count())
            .select_from(AgentRun)
            .where(AgentRun.created_at >= cutoff)
        )
        runs_24h = recent_result.scalar_one()

        unique_result = await db.execute(
            select(func.count(distinct(AgentRun.agent_id)))
        )
        unique_agents = unique_result.scalar_one()

        success_rate = round(success_count / total_runs * 100, 1) if total_runs else 0.0

        return AgentStatsResponse(
            total_runs=total_runs,
            success_rate=success_rate,
            runs_24h=runs_24h,
            unique_agents=unique_agents,
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
