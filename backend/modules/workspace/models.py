"""Workspace module Pydantic models."""

from pydantic import BaseModel


class UsageTier(BaseModel):
    label: str
    percent: int
    resetsIn: str


class UsageResponse(BaseModel):
    model: str
    tiers: list[UsageTier]


class ModelResponse(BaseModel):
    success: bool
    model: str


class HeartbeatResponse(BaseModel):
    lastHeartbeat: int | None = None


class WorkspaceFileResponse(BaseModel):
    content: str
    lastModified: str | None = None


class HistoryEntry(BaseModel):
    timestamp: str
    content: str


class SoulTemplate(BaseModel):
    name: str
    description: str
    content: str
