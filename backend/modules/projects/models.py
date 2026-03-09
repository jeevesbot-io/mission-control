"""Pydantic models for the Projects module."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectDoc(BaseModel):
    title: str
    url: str


class Project(BaseModel):
    id: str
    name: str
    icon: str = ""
    color: str = ""
    description: str | None = None
    docs: list[ProjectDoc] = Field(default_factory=list)
    status: str = "active"
    order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectWithCounts(Project):
    task_count: int = 0
    agent_count: int = 0


class ProjectCreate(BaseModel):
    id: str
    name: str
    icon: str = ""
    color: str = ""
    description: str | None = None
    docs: list[ProjectDoc] = Field(default_factory=list)
    status: str = "active"
    order: int = 0


class ProjectUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    color: str | None = None
    description: str | None = None
    docs: list[ProjectDoc] | None = None
    status: str | None = None
    order: int | None = None


class TaskSummary(BaseModel):
    id: int
    title: str
    state: str
    priority: int
    agent_id: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class ProjectDetail(Project):
    task_count: int = 0
    agent_count: int = 0
    tasks: list[TaskSummary] = Field(default_factory=list)
    agent_ids: list[str] = Field(default_factory=list)
