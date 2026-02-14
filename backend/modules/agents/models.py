"""Pydantic schemas for the Agents module."""

import datetime
from typing import Any

from pydantic import BaseModel


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
