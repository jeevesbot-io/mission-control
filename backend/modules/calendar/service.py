"""Calendar module business logic."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.config import settings

from .models import (
    CalendarEvent,
    CalendarResponse,
    CronJob,
    CronPayload,
)

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for calendar and cron job operations."""

    def __init__(self):
        """Initialize calendar service with OpenClaw gateway config."""
        self.gateway_url = settings.openclaw_gateway_url
        self.gateway_token = settings.openclaw_gateway_token

    async def get_cron_jobs(self) -> list[CronJob]:
        """Fetch all cron jobs from OpenClaw gateway.
        
        NOTE: Direct HTTP access to gateway cron isn't currently exposed.
        This will be implemented when gateway provides an HTTP endpoint for cron listing.
        For now, returns empty list - cron visibility will come later.
        """
        # TODO: Implement when gateway HTTP API exposes cron endpoints
        # The cron tool works internally but isn't accessible via HTTP
        return []

    async def get_upcoming_tasks(self, days_ahead: int = 14) -> list[CalendarEvent]:
        """Get upcoming scheduled tasks from War Room."""
        try:
            # Read tasks from War Room's tasks.json file
            from core.config import settings

            tasks_file = settings.dashboard_data_path / "tasks.json"
            if not tasks_file.exists():
                return []

            with open(tasks_file, "r") as f:
                data = json.load(f)

            tasks = data.get("tasks", [])
            now = datetime.now(timezone.utc)
            cutoff = now + timedelta(days=days_ahead)

            events = []
            for task in tasks:
                # Check if task has a scheduled_for field
                scheduled = task.get("scheduled_for")
                if not scheduled:
                    continue

                # Parse the scheduled time
                try:
                    scheduled_dt = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue

                # Skip past events and events too far in future
                if scheduled_dt < now or scheduled_dt > cutoff:
                    continue

                event = CalendarEvent(
                    id=f"task-{task.get('id', '')}",
                    title=task.get("title", "Untitled Task"),
                    description=task.get("description"),
                    start=scheduled_dt,
                    end=None,
                    type="task",
                    status="scheduled"
                    if task.get("status") in ["todo", "backlog"]
                    else task.get("status", "scheduled"),
                    agent=task.get("assigned_to"),
                    metadata={"task_id": task.get("id")},
                )
                events.append(event)

            return events
        except Exception as e:
            logger.warning("Error fetching upcoming tasks: %s", e)
            return []

    def _cron_to_calendar_events(self, jobs: list[CronJob]) -> list[CalendarEvent]:
        """Convert cron jobs to calendar events."""
        events = []
        now = datetime.now(timezone.utc)

        for job in jobs:
            if not job.enabled:
                continue

            # Determine next run time based on schedule type
            next_run = job.nextRunAt if job.nextRunAt else self._estimate_next_run(job, now)

            if next_run:
                # Extract title from payload
                title = job.name or self._extract_title_from_payload(job.payload)

                event = CalendarEvent(
                    id=job.jobId,
                    title=title,
                    description=self._format_job_description(job),
                    start=next_run,
                    end=None,
                    type="cron",
                    status="scheduled",
                    agent=job.sessionTarget,
                    metadata={
                        "jobId": job.jobId,
                        "schedule": job.schedule.model_dump(),
                        "runCount": job.runCount,
                    },
                )
                events.append(event)

        return events

    def _estimate_next_run(self, job: CronJob, from_time: datetime) -> Optional[datetime]:
        """Estimate next run time for a cron job."""
        schedule = job.schedule

        if schedule.kind == "at" and schedule.at:
            return datetime.fromisoformat(schedule.at.replace("Z", "+00:00"))

        elif schedule.kind == "every" and schedule.everyMs:
            # If we have a last run, use that
            if job.lastRunAt:
                return job.lastRunAt + timedelta(milliseconds=schedule.everyMs)
            # Otherwise use anchor or now
            base = (
                datetime.fromtimestamp(schedule.anchorMs / 1000)
                if schedule.anchorMs
                else from_time
            )
            return base + timedelta(milliseconds=schedule.everyMs)

        elif schedule.kind == "cron":
            # For cron expressions, we'd need a cron parser
            # For now, just return None and rely on nextRunAt from gateway
            return None

        return None

    def _extract_title_from_payload(self, payload: CronPayload) -> str:
        """Extract a readable title from the payload."""
        if payload.kind == "systemEvent" and payload.text:
            # Truncate long text
            text = payload.text[:50]
            return text if len(payload.text) <= 50 else text + "..."
        elif payload.kind == "agentTurn" and payload.message:
            # Truncate long message
            msg = payload.message[:50]
            return msg if len(payload.message) <= 50 else msg + "..."
        return "Scheduled Task"

    def _format_job_description(self, job: CronJob) -> str:
        """Format a human-readable description for a cron job."""
        schedule = job.schedule
        desc_parts = []

        # Schedule description
        if schedule.kind == "at":
            desc_parts.append(f"One-time at {schedule.at}")
        elif schedule.kind == "every" and schedule.everyMs:
            interval = schedule.everyMs / 1000 / 60  # Convert to minutes
            if interval >= 60:
                desc_parts.append(f"Every {interval/60:.1f} hours")
            else:
                desc_parts.append(f"Every {interval:.0f} minutes")
        elif schedule.kind == "cron":
            desc_parts.append(f"Cron: {schedule.expr}")

        # Payload type
        desc_parts.append(f"Type: {job.payload.kind}")

        # Session target
        desc_parts.append(f"Session: {job.sessionTarget}")

        return " | ".join(desc_parts)

    async def get_calendar(
        self, start_date: Optional[datetime] = None, days_ahead: int = 14
    ) -> CalendarResponse:
        """Get full calendar with cron jobs and tasks."""
        # Fetch cron jobs from gateway
        cron_jobs = await self.get_cron_jobs()

        # Convert cron jobs to calendar events
        cron_events = self._cron_to_calendar_events(cron_jobs)

        # Fetch upcoming tasks from War Room
        task_events = await self.get_upcoming_tasks(days_ahead)

        # Combine all events
        all_events = cron_events + task_events

        # Sort by start time
        all_events.sort(key=lambda e: e.start)

        return CalendarResponse(events=all_events, cronJobs=cron_jobs)


calendar_service = CalendarService()
