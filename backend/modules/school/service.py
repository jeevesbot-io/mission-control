"""School module service — queries existing school_emails, school_events, todoist_tasks tables."""

import datetime
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SchoolEmail, SchoolEvent, SchoolStatsResponse, TodoistTask

logger = logging.getLogger(__name__)


class SchoolService:
    """Query existing Postgres school tables."""

    async def get_events(
        self, db: AsyncSession, limit: int = 50
    ) -> list[SchoolEvent]:
        """Get upcoming school events."""
        try:
            result = await db.execute(
                text("""
                    SELECT id, title, description, start_time, end_time, location, all_day
                    FROM school_events
                    WHERE start_time >= NOW() - INTERVAL '1 day'
                    ORDER BY start_time ASC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            return [
                SchoolEvent(
                    id=row.id,
                    title=row.title,
                    description=row.description,
                    start_time=row.start_time,
                    end_time=row.end_time,
                    location=row.location,
                    all_day=row.all_day,
                )
                for row in result.fetchall()
            ]
        except Exception as exc:
            logger.warning("Failed to query school_events: %s", exc)
            return []

    async def get_emails(
        self, db: AsyncSession, limit: int = 50
    ) -> list[SchoolEmail]:
        """Get recent school emails."""
        try:
            result = await db.execute(
                text("""
                    SELECT id, subject, sender, preview, received_at, is_read
                    FROM school_emails
                    ORDER BY received_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            return [
                SchoolEmail(
                    id=row.id,
                    subject=row.subject,
                    sender=row.sender,
                    preview=row.preview,
                    received_at=row.received_at,
                    is_read=row.is_read,
                )
                for row in result.fetchall()
            ]
        except Exception as exc:
            logger.warning("Failed to query school_emails: %s", exc)
            return []

    async def get_tasks(
        self, db: AsyncSession, limit: int = 50
    ) -> list[TodoistTask]:
        """Get todoist tasks/action items."""
        try:
            result = await db.execute(
                text("""
                    SELECT id, content, description, priority, due_date, is_completed, project_name
                    FROM todoist_tasks
                    ORDER BY priority DESC, due_date ASC NULLS LAST
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            return [
                TodoistTask(
                    id=str(row.id),
                    content=row.content,
                    description=row.description,
                    priority=row.priority,
                    due_date=row.due_date,
                    is_completed=row.is_completed,
                    project_name=row.project_name,
                )
                for row in result.fetchall()
            ]
        except Exception as exc:
            logger.warning("Failed to query todoist_tasks: %s", exc)
            return []

    async def get_stats(self, db: AsyncSession) -> SchoolStatsResponse:
        """Counts and summaries for overview."""
        try:
            events_result = await db.execute(
                text("""
                    SELECT COUNT(*) FROM school_events
                    WHERE start_time >= NOW() AND start_time < NOW() + INTERVAL '7 days'
                """)
            )
            upcoming_events = events_result.scalar_one()
        except Exception:
            upcoming_events = 0

        try:
            emails_result = await db.execute(
                text("SELECT COUNT(*) FROM school_emails WHERE is_read = false")
            )
            unread_emails = emails_result.scalar_one()
        except Exception:
            unread_emails = 0

        try:
            tasks_result = await db.execute(
                text("SELECT COUNT(*) FROM todoist_tasks WHERE is_completed = false")
            )
            pending_tasks = tasks_result.scalar_one()
        except Exception:
            pending_tasks = 0

        try:
            today = datetime.date.today()
            completed_result = await db.execute(
                text("""
                    SELECT COUNT(*) FROM todoist_tasks
                    WHERE is_completed = true
                    AND completed_at >= :today
                """),
                {"today": today},
            )
            completed_today = completed_result.scalar_one()
        except Exception:
            completed_today = 0

        return SchoolStatsResponse(
            upcoming_events=upcoming_events,
            unread_emails=unread_emails,
            pending_tasks=pending_tasks,
            completed_today=completed_today,
        )


school_service = SchoolService()
