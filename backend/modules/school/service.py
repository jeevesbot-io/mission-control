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
                    SELECT id, child, summary, description, event_date, event_end_date,
                           event_time::text as event_time, school_id
                    FROM school_events
                    WHERE event_date >= CURRENT_DATE - INTERVAL '1 day'
                    ORDER BY event_date ASC, event_time ASC NULLS LAST
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            return [
                SchoolEvent(
                    id=row.id,
                    child=row.child,
                    summary=row.summary,
                    description=row.description,
                    event_date=row.event_date.isoformat() if row.event_date else None,
                    event_end_date=row.event_end_date.isoformat() if row.event_end_date else None,
                    event_time=row.event_time,
                    school_id=row.school_id,
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
                    SELECT id, email_id, subject, sender, child, school_id,
                           LEFT(body_text, 200) as preview, processed_at
                    FROM school_emails
                    ORDER BY processed_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            return [
                SchoolEmail(
                    id=row.id,
                    email_id=row.email_id,
                    subject=row.subject,
                    sender=row.sender,
                    child=row.child,
                    school_id=row.school_id,
                    preview=row.preview,
                    processed_at=row.processed_at,
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
                    SELECT id, content, description, due_date, todoist_id, created_at
                    FROM todoist_tasks
                    ORDER BY due_date ASC NULLS LAST, created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            return [
                TodoistTask(
                    id=str(row.id),
                    content=row.content,
                    description=row.description,
                    due_date=row.due_date.isoformat() if row.due_date else None,
                    todoist_id=row.todoist_id,
                    created_at=row.created_at,
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
                    WHERE event_date >= CURRENT_DATE
                      AND event_date < CURRENT_DATE + INTERVAL '7 days'
                """)
            )
            upcoming_events = events_result.scalar_one()
        except Exception:
            upcoming_events = 0

        try:
            emails_result = await db.execute(
                text("SELECT COUNT(*) FROM school_emails")
            )
            total_emails = emails_result.scalar_one()
        except Exception:
            total_emails = 0

        try:
            tasks_result = await db.execute(
                text("SELECT COUNT(*) FROM todoist_tasks")
            )
            total_tasks = tasks_result.scalar_one()
        except Exception:
            total_tasks = 0

        return SchoolStatsResponse(
            upcoming_events=upcoming_events,
            total_emails=total_emails,
            total_tasks=total_tasks,
        )


school_service = SchoolService()
