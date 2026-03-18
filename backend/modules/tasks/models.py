"""Tasks module Pydantic models — camelCase API shape matching the warroom frontend."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

TaskStatus = Literal[
    "backlog", "todo", "in-progress", "blocked", "peer_review", "rejected", "review", "done", "cancelled"
]
TaskPriority = Literal["low", "medium", "high", "urgent"]
TaskType = Literal["feature", "bug", "debt", "investigation", "chore"]

# Maps API priority string <-> Postgres integer
PRIORITY_STR_TO_INT: dict[str, int] = {"urgent": 1, "high": 2, "medium": 3, "low": 4}
PRIORITY_INT_TO_STR: dict[int, str] = {v: k for k, v in PRIORITY_STR_TO_INT.items()}

# Maps API status (hyphenated) <-> Postgres state (underscored)
VALID_STATES = {
    "backlog", "todo", "in_progress", "blocked",
    "peer_review", "rejected", "review", "done", "cancelled",
}


def status_to_state(status: str) -> str:
    """Convert API status string to Postgres state value."""
    return status.replace("-", "_")


def state_to_status(state: str) -> str:
    """Convert Postgres state value to API status string."""
    return state.replace("_", "-") if state == "in_progress" else state


# --- API response model (camelCase, matching warroom Task shape) ---


class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    status: TaskStatus = "backlog"
    priority: TaskPriority = "medium"
    type: TaskType = "feature"
    project: str | None = None
    tags: list[str] = []
    skill: str | None = None
    schedule: str | None = None
    scheduledAt: str | None = None
    references: list[dict] = []
    blockedBy: list[str] = []
    blocks: list[str] = []
    startedAt: str | None = None
    completedAt: str | None = None
    result: str | None = None
    error: str | None = None
    pickedUp: bool = False
    createdAt: str
    updatedAt: str
    estimatedHours: float | None = None
    actualHours: float | None = None
    slug: str | None = None


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: TaskPriority = "medium"
    status: TaskStatus = "backlog"
    type: TaskType = "feature"
    project: str | None = None
    tags: list[str] = []
    skill: str | None = None
    schedule: str | None = None
    scheduledAt: str | None = None
    blockedBy: list[str] = []
    estimatedHours: float | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    type: TaskType | None = None
    project: str | None = None
    tags: list[str] | None = None
    skill: str | None = None
    schedule: str | None = None
    scheduledAt: str | None = None
    blockedBy: list[str] | None = None
    blocks: list[str] | None = None
    result: str | None = None
    error: str | None = None
    startedAt: str | None = None
    completedAt: str | None = None
    estimatedHours: float | None = None
    actualHours: float | None = None


class TaskComplete(BaseModel):
    result: str | None = None
    error: str | None = None


class TaskStats(BaseModel):
    in_progress_count: int
    todo_count: int
    last_heartbeat: int | None
    active_model: str
