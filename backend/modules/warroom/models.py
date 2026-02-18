"""War Room module Pydantic models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

# Priority order for queue sorting (lower = higher priority)
PRIORITY_ORDER: dict[str, int] = {"urgent": 0, "high": 1, "medium": 2, "low": 3}

TaskStatus = Literal["backlog", "todo", "in-progress", "done"]
TaskPriority = Literal["low", "medium", "high", "urgent"]
ReferenceType = Literal["link", "obsidian", "doc"]
ProjectStatus = Literal["active", "paused", "archived"]
SkillSource = Literal["bundled", "managed", "workspace"]


# --- References ---

class Reference(BaseModel):
    id: str
    title: str
    url: str
    type: ReferenceType = "link"
    createdAt: str


class ReferenceCreate(BaseModel):
    title: str
    url: str
    type: ReferenceType | None = None  # auto-detected if omitted


# --- Tasks ---

class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    status: TaskStatus = "backlog"
    priority: TaskPriority = "medium"
    project: str | None = None
    tags: list[str] = []
    skill: str | None = None
    schedule: str | None = None
    scheduledAt: str | None = None
    references: list[Reference] = []
    startedAt: str | None = None
    completedAt: str | None = None
    result: str | None = None
    error: str | None = None
    pickedUp: bool = False
    createdAt: str
    updatedAt: str
    estimatedHours: float | None = None
    actualHours: float | None = None


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: TaskPriority = "medium"
    status: TaskStatus = "backlog"
    project: str | None = None
    tags: list[str] = []
    skill: str | None = None
    schedule: str | None = None
    scheduledAt: str | None = None
    estimatedHours: float | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    project: str | None = None
    tags: list[str] | None = None
    skill: str | None = None
    schedule: str | None = None
    scheduledAt: str | None = None
    result: str | None = None
    error: str | None = None
    startedAt: str | None = None
    completedAt: str | None = None
    estimatedHours: float | None = None
    actualHours: float | None = None


class TaskComplete(BaseModel):
    result: str | None = None
    error: str | None = None


# --- Projects ---

class Project(BaseModel):
    id: str
    name: str
    icon: str
    color: str
    description: str | None = None
    status: ProjectStatus = "active"
    order: int = 0


class ProjectCreate(BaseModel):
    id: str
    name: str
    icon: str
    color: str
    description: str | None = None
    status: ProjectStatus = "active"
    order: int = 0


class ProjectUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    color: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    order: int | None = None


class ProjectWithCount(Project):
    task_count: int = 0


# --- Usage / Models ---

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


# --- Heartbeat ---

class HeartbeatResponse(BaseModel):
    lastHeartbeat: int | None = None


# --- Skills ---

class Skill(BaseModel):
    id: str
    name: str
    description: str = ""
    source: SkillSource
    enabled: bool = True
    path: str
    hasMetadata: bool = False


class SkillCreate(BaseModel):
    name: str
    description: str = ""
    instructions: str = ""


# --- Workspace Files / Soul ---

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


# --- Calendar ---

class CalendarDay(BaseModel):
    memory: bool = False
    tasks: list[str] = []


# --- Stats (for overview widget) ---

class WarRoomStats(BaseModel):
    in_progress_count: int
    todo_count: int
    last_heartbeat: int | None
    active_model: str
