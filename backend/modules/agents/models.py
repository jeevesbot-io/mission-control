"""Pydantic schemas for the Agents module."""

import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    agent_id: str
    last_activity: datetime.datetime | None
    last_message: str | None
    last_level: str | None
    total_entries: int
    warning_count: int


class AgentLogEntry(BaseModel):
    id: int
    agent_id: str
    level: str
    message: str
    metadata: dict[str, Any] | None
    created_at: datetime.datetime


class AgentLogPage(BaseModel):
    entries: list[AgentLogEntry]
    total: int
    page: int
    page_size: int


class CronJob(BaseModel):
    agent_id: str
    schedule: str
    enabled: bool
    last_run: str | None = None
    next_run: str | None = None


class CronResponse(BaseModel):
    jobs: list[CronJob]


class TriggerResponse(BaseModel):
    success: bool
    message: str
    agent_id: str


class AgentStatsResponse(BaseModel):
    total_entries: int
    unique_agents: int
    entries_24h: int
    warning_count: int
    health_rate: float


class AgentMetadata(BaseModel):
    agent_id: str
    display_name: str
    role: str
    model: str
    tier: str
    workspace: str
    can_spawn: bool
    responsibilities: list[str]


class AgentDetailResponse(BaseModel):
    agent_id: str
    display_name: str
    role: str
    model: str
    tier: str
    status: str  # active / idle / offline
    last_activity: datetime.datetime | None
    last_message: str | None
    last_level: str | None
    total_entries: int
    warning_count: int
    tasks_in_progress: int
    tasks_assigned: int
    responsibilities: list[str]


class AgentWorkstation(BaseModel):
    """Agent workstation representation for office view."""

    agent_id: str
    display_name: str
    avatar_color: str
    status: Literal["active", "idle", "working", "scheduled", "offline"]
    current_task: Optional[str] = None
    last_seen: Optional[datetime.datetime] = None
    position: dict = Field(default_factory=dict)  # x, y coordinates
    metadata: dict = Field(default_factory=dict)


class OfficeViewResponse(BaseModel):
    """Response containing office view data."""

    workstations: list[AgentWorkstation]
    office_stats: dict = Field(default_factory=dict)


class LiveSession(BaseModel):
    """Live agent session from OpenClaw sessions API."""

    session_key: str = ""
    agent_id: str = ""
    state: str = "unknown"
    created_at: str = ""
    last_activity: str = ""
    elapsed_seconds: int = 0
    task: str = ""
    channel: str = ""
    message_count: int = 0
