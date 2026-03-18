"""Agent Runs module Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRun(BaseModel):
    """Full agent_runs row — response model."""

    id: UUID
    agent_id: str
    run_type: str
    trigger: str
    status: str
    summary: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    metadata: Optional[dict] = None
    prompt_preview: Optional[str] = None
    channel: Optional[str] = None
    session_key: Optional[str] = None
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    created_at: datetime


class AgentRunCreate(BaseModel):
    """POST /ingest request body."""

    agent_id: str
    run_type: str = "task"
    trigger: str = "system"
    status: str = "completed"
    summary: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    metadata: Optional[dict] = None
    prompt_preview: Optional[str] = None
    channel: Optional[str] = None
    session_key: Optional[str] = None
    outcome: Optional[str] = None


class AgentRunList(BaseModel):
    """Paginated response."""

    items: list[AgentRun]
    total: int
    page: int
    page_size: int


class AgentCount(BaseModel):
    """Per-agent count within a heatmap day."""

    agent_id: str
    count: int


class HeatmapDay(BaseModel):
    """Daily aggregate for heatmap."""

    date: str
    count: int
    agents: list[AgentCount] = Field(default_factory=list)


class DayDetail(BaseModel):
    """All runs for a specific day."""

    date: str
    runs: list[AgentRun]
