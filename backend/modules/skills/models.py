"""Pydantic models for the Skills module."""

import datetime

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
