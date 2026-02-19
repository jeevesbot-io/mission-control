"""Activity module Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ActivityEvent(BaseModel):
    """A single activity event."""

    id: str
    timestamp: datetime
    actor: str  # "user", "system", or agent_id
    action: str  # "task.created", "agent.triggered", etc.
    resource_type: str  # "task", "agent", "model", "skill", "soul", "content"
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    details: dict = Field(default_factory=dict)
    module: str  # "warroom", "agents", "content", etc.


class ActivityFeedResponse(BaseModel):
    """Paginated activity feed."""

    events: list[ActivityEvent]
    total: int
    cursor: Optional[str] = None  # ISO timestamp of last event for pagination


class ActivityStats(BaseModel):
    """Activity statistics."""

    total_events: int
    by_module: dict[str, int] = Field(default_factory=dict)
    by_action: dict[str, int] = Field(default_factory=dict)
    last_24h: int = 0


class ActivityLogRequest(BaseModel):
    """Request to log an activity event."""

    actor: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    details: dict = Field(default_factory=dict)
    module: str
