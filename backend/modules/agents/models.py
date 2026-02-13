"""Pydantic schemas for the Agents module."""

import datetime

from pydantic import BaseModel


class AgentInfo(BaseModel):
    agent_id: str
    last_run: datetime.datetime | None
    last_status: str | None
    total_runs: int


class AgentRunResponse(BaseModel):
    id: str
    agent_id: str
    run_type: str
    trigger: str
    status: str
    summary: str | None
    duration_ms: int | None
    tokens_used: int | None
    created_at: datetime.datetime


class AgentRunsPage(BaseModel):
    runs: list[AgentRunResponse]
    total: int
    page: int
    page_size: int


class CronJob(BaseModel):
    agent_id: str
    schedule: str
    enabled: bool
    last_run: str | None
    next_run: str | None


class CronResponse(BaseModel):
    jobs: list[CronJob]


class TriggerResponse(BaseModel):
    success: bool
    message: str
    agent_id: str


class AgentStatsResponse(BaseModel):
    total_runs: int
    success_rate: float
    runs_24h: int
    unique_agents: int
