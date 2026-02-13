"""Overview module service — aggregates data from all sources."""

import datetime
import logging
import time

from sqlalchemy import distinct, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import AgentRun

from .models import (
    AgentStatusSummary,
    OverviewResponse,
    OverviewStats,
    RecentActivity,
    SystemHealth,
    UpcomingEvent,
)

logger = logging.getLogger(__name__)

_start_time = time.monotonic()


class OverviewService:
    """Aggregates overview data from multiple sources."""

    async def get_overview(self, db: AsyncSession) -> OverviewResponse:
        """Build the complete overview response."""
        agent_summary = await self._get_agent_summary(db)
        upcoming_events = await self._get_upcoming_events(db)
        recent_activity = await self._get_recent_activity(db)
        health = await self._get_health(db)
        stats = await self._get_stats(db, agent_summary, upcoming_events)

        return OverviewResponse(
            stats=stats,
            agent_summary=agent_summary,
            upcoming_events=upcoming_events,
            recent_activity=recent_activity,
            health=health,
        )

    async def _get_agent_summary(self, db: AsyncSession) -> AgentStatusSummary:
        """Query agent_runs for summary stats."""
        try:
            total_result = await db.execute(
                select(func.count()).select_from(AgentRun)
            )
            total_runs = total_result.scalar_one()

            if total_runs == 0:
                return AgentStatusSummary(
                    total_runs=0,
                    success_count=0,
                    failure_count=0,
                    runs_24h=0,
                    unique_agents=0,
                    success_rate=0.0,
                )

            success_result = await db.execute(
                select(func.count())
                .select_from(AgentRun)
                .where(AgentRun.status == "success")
            )
            success_count = success_result.scalar_one()

            failure_result = await db.execute(
                select(func.count())
                .select_from(AgentRun)
                .where(AgentRun.status.in_(["error", "failed"]))
            )
            failure_count = failure_result.scalar_one()

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

            success_rate = round(success_count / total_runs * 100, 1)

            return AgentStatusSummary(
                total_runs=total_runs,
                success_count=success_count,
                failure_count=failure_count,
                runs_24h=runs_24h,
                unique_agents=unique_agents,
                success_rate=success_rate,
            )
        except Exception as exc:
            logger.warning("Failed to get agent summary: %s", exc)
            return AgentStatusSummary(
                total_runs=0,
                success_count=0,
                failure_count=0,
                runs_24h=0,
                unique_agents=0,
                success_rate=0.0,
            )

    async def _get_upcoming_events(self, db: AsyncSession) -> list[UpcomingEvent]:
        """Query school_events for the next 7 days."""
        try:
            today = datetime.date.today()
            week_end = today + datetime.timedelta(days=7)

            result = await db.execute(
                text("""
                    SELECT id, child, summary, event_date, event_end_date,
                           event_time::text as event_time
                    FROM school_events
                    WHERE event_date >= :today AND event_date <= :week_end
                    ORDER BY event_date ASC, event_time ASC NULLS LAST
                    LIMIT 20
                """),
                {"today": today, "week_end": week_end},
            )

            events = []
            for row in result.fetchall():
                days_away = (row.event_date - today).days
                events.append(
                    UpcomingEvent(
                        id=row.id,
                        child=row.child or "Unknown",
                        summary=row.summary or "Untitled event",
                        event_date=row.event_date.isoformat(),
                        event_end_date=(
                            row.event_end_date.isoformat() if row.event_end_date else None
                        ),
                        event_time=row.event_time,
                        days_away=days_away,
                    )
                )
            return events
        except Exception as exc:
            logger.warning("Failed to get upcoming events: %s", exc)
            return []

    async def _get_recent_activity(self, db: AsyncSession) -> list[RecentActivity]:
        """Get the last 10 agent runs."""
        try:
            result = await db.execute(
                select(AgentRun)
                .order_by(AgentRun.created_at.desc())
                .limit(10)
            )
            return [
                RecentActivity(
                    id=str(run.id),
                    agent_id=run.agent_id,
                    run_type=run.run_type,
                    trigger=run.trigger,
                    status=run.status,
                    summary=run.summary,
                    duration_ms=run.duration_ms,
                    created_at=run.created_at,
                )
                for run in result.scalars().all()
            ]
        except Exception as exc:
            logger.warning("Failed to get recent activity: %s", exc)
            return []

    async def _get_health(self, db: AsyncSession) -> SystemHealth:
        """Check system health."""
        db_ok = False
        try:
            await db.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            pass

        uptime = time.monotonic() - _start_time
        status = "healthy" if db_ok else "degraded"

        return SystemHealth(
            status=status,
            database=db_ok,
            uptime_seconds=round(uptime, 1),
            version="0.1.0",
        )

    async def _get_stats(
        self,
        db: AsyncSession,
        agent_summary: AgentStatusSummary,
        upcoming_events: list[UpcomingEvent],
    ) -> OverviewStats:
        """Build the top-level stat cards."""
        # Emails processed (count from school_emails)
        emails_processed = 0
        try:
            result = await db.execute(text("SELECT COUNT(*) FROM school_emails"))
            emails_processed = result.scalar_one()
        except Exception:
            pass

        # Tasks pending
        tasks_pending = 0
        try:
            result = await db.execute(
                text("SELECT COUNT(*) FROM todoist_tasks WHERE is_completed = false")
            )
            tasks_pending = result.scalar_one()
        except Exception:
            pass

        return OverviewStats(
            agents_active=agent_summary.unique_agents,
            events_this_week=len(upcoming_events),
            emails_processed=emails_processed,
            tasks_pending=tasks_pending,
        )


overview_service = OverviewService()
