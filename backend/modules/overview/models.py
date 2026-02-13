"""Pydantic schemas for the Overview module."""

import datetime

from pydantic import BaseModel


class AgentStatusSummary(BaseModel):
    total_runs: int
    success_count: int
    failure_count: int
    runs_24h: int
    unique_agents: int
    success_rate: float


class UpcomingEvent(BaseModel):
    id: int
    child: str
    summary: str
    event_date: str  # ISO date string
    event_end_date: str | None
    event_time: str | None
    days_away: int


class RecentActivity(BaseModel):
    id: str
    agent_id: str
    run_type: str
    trigger: str
    status: str
    summary: str | None
    duration_ms: int | None
    created_at: datetime.datetime


class SystemHealth(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
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
