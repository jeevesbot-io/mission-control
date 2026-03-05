"""Pydantic schemas for the Overview module."""

import datetime

from pydantic import BaseModel


class AgentStatusSummary(BaseModel):
    total_entries: int
    info_count: int
    warning_count: int
    entries_24h: int
    unique_agents: int
    health_rate: float


class UpcomingEvent(BaseModel):
    id: int
    child: str
    summary: str
    event_date: str
    event_end_date: str | None
    event_time: str | None
    days_away: int


class RecentActivity(BaseModel):
    id: str
    agent_id: str
    level: str
    message: str
    created_at: datetime.datetime


class SystemHealth(BaseModel):
    status: str
    database: bool
    uptime_seconds: float
    version: str


class OverviewStats(BaseModel):
    agents_active: int
    events_this_week: int
    emails_processed: int
    tasks_pending: int


class OverviewResponse(BaseModel):
    stats: OverviewStats
    agent_summary: AgentStatusSummary
    upcoming_events: list[UpcomingEvent]
    recent_activity: list[RecentActivity]
    health: SystemHealth


class TaskQueueItem(BaseModel):
    id: int
    title: str
    state: str
    agent_id: str
    priority: int
    labels: list[str] | None


class AgentActivityItem(BaseModel):
    agent_id: str
    action: str
    detail: str | None
    created_at: datetime.datetime


class StandupResponse(BaseModel):
    date: str
    task_queue: list[TaskQueueItem]
    tasks_done_24h: int
    tasks_in_progress: int
    tasks_in_review: int
    recent_agent_activity: list[AgentActivityItem]
    upcoming_events: list[UpcomingEvent]
    blockers: list[TaskQueueItem]
