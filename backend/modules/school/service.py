"""School module service — queries school tables + Google Calendar via gog CLI."""

import asyncio
import datetime
import json
import logging
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    CalendarEvent,
    CalendarEventsResponse,
    SchoolEmail,
    SchoolEvent,
    SchoolStatsResponse,
    TodoistTask,
)

from core.config import settings

logger = logging.getLogger(__name__)

CALENDAR_ACCOUNT = "sollyfamily3@gmail.com"

# Patterns to infer which child an event relates to
CHILD_PATTERNS = [
    (re.compile(r"\bnatty\b", re.I), "Natty"),
    (re.compile(r"\belodie\b", re.I), "Elodie"),
    (re.compile(r"\bflorence\b", re.I), "Florence"),
    (re.compile(r"\bQE\b"), "Natty"),
    (re.compile(r"\bCounty\b", re.I), "Elodie"),
    (re.compile(r"\bOnslow\b", re.I), "Florence"),
]


def _infer_child(summary: str) -> str | None:
    """Try to match a child from event summary."""
    for pattern, child in CHILD_PATTERNS:
        if pattern.search(summary):
            return child
    return None


class SchoolService:
    """Query existing Postgres school tables + Google Calendar."""

    async def get_calendar_events(self, days: int = 7) -> CalendarEventsResponse:
        """Fetch events from Google Calendar via gog CLI."""
        today = datetime.date.today()
        window_end = today + datetime.timedelta(days=days)

        # When gog_path is empty, calendar is disabled (e.g. in Docker)
        if not settings.gog_path:
            return CalendarEventsResponse(
                events=[], total=0,
                window_start=today.isoformat(),
                window_end=window_end.isoformat(),
            )

        from_iso = f"{today.isoformat()}T00:00:00Z"
        to_iso = f"{window_end.isoformat()}T00:00:00Z"

        try:
            proc = await asyncio.create_subprocess_exec(
                settings.gog_path, "calendar", "events", "primary",
                "--account", CALENDAR_ACCOUNT,
                "--from", from_iso,
                "--to", to_iso,
                "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)

            if proc.returncode != 0:
                logger.warning("gog calendar failed (rc=%d): %s", proc.returncode, stderr.decode())
                return CalendarEventsResponse(
                    events=[], total=0,
                    window_start=today.isoformat(),
                    window_end=window_end.isoformat(),
                )

            data = json.loads(stdout.decode())
            raw_events = data.get("events", [])

            # gog paginates — fetch remaining pages
            while data.get("nextPageToken"):
                proc2 = await asyncio.create_subprocess_exec(
                    settings.gog_path, "calendar", "events", "primary",
                    "--account", CALENDAR_ACCOUNT,
                    "--from", from_iso,
                    "--to", to_iso,
                    "--json",
                    "--page", data["nextPageToken"],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout2, _ = await asyncio.wait_for(proc2.communicate(), timeout=15)
                if proc2.returncode != 0:
                    break
                data = json.loads(stdout2.decode())
                raw_events.extend(data.get("events", []))

            events = []
            for raw in raw_events:
                summary = raw.get("summary", "(No title)")
                start = raw.get("start", {})
                end = raw.get("end", {})
                all_day = "date" in start and "dateTime" not in start

                events.append(CalendarEvent(
                    id=raw.get("id", ""),
                    summary=summary,
                    start_date=start.get("date"),
                    start_datetime=start.get("dateTime"),
                    end_date=end.get("date"),
                    end_datetime=end.get("dateTime"),
                    all_day=all_day,
                    child=_infer_child(summary),
                ))

            # Sort: timed events by datetime, all-day by date
            events.sort(key=lambda e: e.start_datetime or f"{e.start_date}T00:00:00Z")

            return CalendarEventsResponse(
                events=events,
                total=len(events),
                window_start=today.isoformat(),
                window_end=window_end.isoformat(),
            )

        except asyncio.TimeoutError:
            logger.warning("gog calendar timed out")
            return CalendarEventsResponse(
                events=[], total=0,
                window_start=today.isoformat(),
                window_end=window_end.isoformat(),
            )
        except Exception as exc:
            logger.warning("Failed to fetch calendar: %s", exc)
            return CalendarEventsResponse(
                events=[], total=0,
                window_start=today.isoformat(),
                window_end=window_end.isoformat(),
            )

    async def get_events(
        self, db: AsyncSession, limit: int = 50
    ) -> list[SchoolEvent]:
        """Get upcoming school events from DB."""
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
        # Calendar events count from gog
        try:
            cal = await self.get_calendar_events(days=7)
            upcoming_events = cal.total
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
