"""Overview module service — aggregates data from all sources."""

import datetime
import logging
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
        """Query agent_log for summary stats."""
        try:
            result = await db.execute(
                text("""
                    SELECT
                        COUNT(*) as total_entries,
                        COUNT(*) FILTER (WHERE level IN ('info', 'INFO')) as info_count,
                        COUNT(*) FILTER (WHERE level IN ('warning', 'WARNING', 'error', 'ERROR')) as warning_count,
                        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as entries_24h,
                        COUNT(DISTINCT agent) as unique_agents
                    FROM agent_log
                """)
            )
            row = result.fetchone()

            if not row or row.total_entries == 0:
                return AgentStatusSummary(
                    total_entries=0,
                    info_count=0,
                    warning_count=0,
                    entries_24h=0,
                    unique_agents=0,
                    health_rate=100.0,
                )

            health_rate = round(row.info_count / row.total_entries * 100, 1)

            return AgentStatusSummary(
                total_entries=row.total_entries,
                info_count=row.info_count,
                warning_count=row.warning_count,
                entries_24h=row.entries_24h,
                unique_agents=row.unique_agents,
                health_rate=health_rate,
            )
        except Exception as exc:
            logger.warning("Failed to get agent summary: %s", exc)
            return AgentStatusSummary(
                total_entries=0,
                info_count=0,
                warning_count=0,
                entries_24h=0,
                unique_agents=0,
                health_rate=0.0,
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
        """Get the last 10 agent log entries."""
        try:
            result = await db.execute(
                text("""
                    SELECT id, agent, level, message, metadata, created_at
                    FROM agent_log
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
            )
            return [
                RecentActivity(
                    id=str(row.id),
                    agent_id=row.agent,
                    level=row.level.lower(),
                    message=row.message,
                    created_at=row.created_at,
                )
                for row in result.fetchall()
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
        emails_processed = 0
        try:
            result = await db.execute(text("SELECT COUNT(*) FROM school_emails"))
            emails_processed = result.scalar_one()
        except Exception:
            pass

        tasks_total = 0
        try:
            result = await db.execute(text("SELECT COUNT(*) FROM todoist_tasks"))
            tasks_total = result.scalar_one()
        except Exception:
            pass

        return OverviewStats(
            agents_active=agent_summary.unique_agents,
            events_this_week=len(upcoming_events),
            emails_processed=emails_processed,
            tasks_pending=tasks_total,
        )


overview_service = OverviewService()
