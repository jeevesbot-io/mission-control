"""Pydantic models for the Skills Browser module."""

from pydantic import BaseModel


class SkillSummary(BaseModel):
    name: str
    description: str
    source: str


class SkillDetail(BaseModel):
    name: str
    content: str
