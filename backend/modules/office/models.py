"""Office module Pydantic models."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentWorkstation(BaseModel):
    """Agent workstation representation."""

    agent_id: str
    display_name: str
    avatar_color: str
    status: Literal["active", "idle", "working", "scheduled", "offline"]
    current_task: Optional[str] = None
    last_seen: Optional[datetime] = None
    position: dict = Field(default_factory=dict)  # x, y coordinates
    metadata: dict = Field(default_factory=dict)


class OfficeResponse(BaseModel):
    """Response containing office view data."""

    workstations: list[AgentWorkstation]
    office_stats: dict = Field(default_factory=dict)
