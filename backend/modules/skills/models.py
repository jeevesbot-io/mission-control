"""Pydantic models for the Skills module."""

import datetime
from typing import Any

from pydantic import BaseModel


class SkillSummary(BaseModel):
    id: int | None = None
    name: str
    description: str
    source: str
    source_label: str | None = None
    file_count: int | None = None
    sha256_hash: str | None = None
    last_indexed_at: datetime.datetime | None = None
    last_changed_at: datetime.datetime | None = None
    has_drift: bool = False


class SkillDetail(BaseModel):
    name: str
    content: str
    source_label: str | None = None
    sha256_hash: str | None = None
    last_changed_at: datetime.datetime | None = None


class ReindexRequest(BaseModel):
    source: str | None = None


class ReindexResult(BaseModel):
    indexed: int
    drifted: int
    new: int
    removed: int
    duration_ms: int


class DriftEntry(BaseModel):
    """A single drift log entry with skill context."""

    skill_name: str
    source_label: str
    old_hash: str
    new_hash: str
    old_file_count: int | None = None
    new_file_count: int | None = None
    files_changed: list[dict[str, Any]] | None = None
    detected_at: datetime.datetime


class SkillStats(BaseModel):
    """Overview statistics for the Skills Hub War Room widget."""

    total_skills: int
    by_source: dict[str, int]
    drifted_last_7d: int
    last_full_index: datetime.datetime | None = None
