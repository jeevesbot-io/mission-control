"""Calendar module Pydantic models."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CronSchedule(BaseModel):
    """Cron job schedule definition."""

    kind: Literal["at", "every", "cron"]
    at: Optional[str] = None  # ISO-8601 timestamp for "at"
    everyMs: Optional[int] = None  # Interval in ms for "every"
    anchorMs: Optional[int] = None  # Start time for "every"
    expr: Optional[str] = None  # Cron expression for "cron"
    tz: Optional[str] = None  # Timezone for "cron"


class CronPayload(BaseModel):
    """Cron job payload definition."""

    kind: Literal["systemEvent", "agentTurn"]
    text: Optional[str] = None  # For systemEvent
    message: Optional[str] = None  # For agentTurn
    model: Optional[str] = None
    thinking: Optional[str] = None
    timeoutSeconds: Optional[int] = None


class CronDelivery(BaseModel):
    """Cron job delivery configuration."""

    mode: Optional[Literal["none", "announce", "webhook"]] = "announce"
    channel: Optional[str] = None
    to: Optional[str] = None
    bestEffort: Optional[bool] = None


class CronJob(BaseModel):
    """Cron job representation."""

    jobId: str
    name: Optional[str] = None
    schedule: CronSchedule
    payload: CronPayload
    delivery: Optional[CronDelivery] = None
    sessionTarget: Literal["main", "isolated"]
    enabled: bool = True
    createdAt: Optional[datetime] = None
    nextRunAt: Optional[datetime] = None
    lastRunAt: Optional[datetime] = None
    runCount: int = 0


class CronJobsResponse(BaseModel):
    """Response containing all cron jobs."""

    jobs: list[CronJob]
    total: int


class CalendarEvent(BaseModel):
    """Calendar event representing a scheduled task."""

    id: str
    title: str
    description: Optional[str] = None
    start: datetime
    end: Optional[datetime] = None
    type: Literal["cron", "task", "reminder"]
    status: Literal["scheduled", "running", "completed", "failed"]
    agent: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class CalendarResponse(BaseModel):
    """Response containing calendar events."""

    events: list[CalendarEvent]
    cronJobs: list[CronJob]
