"""Content module Pydantic models."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    """Content item representation."""

    id: str
    title: str
    description: Optional[str] = None
    stage: Literal["ideas", "scripting", "thumbnail", "filming", "editing", "published"]
    type: Literal["video", "article", "thread", "tweet", "other"] = "video"
    script: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    published_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    assigned_to: Optional[Literal["human", "agent"]] = None
    priority: Literal["low", "medium", "high"] = "medium"
    created_at: datetime
    updated_at: datetime
    metadata: dict = Field(default_factory=dict)


class ContentCreate(BaseModel):
    """Create content item request."""

    title: str
    description: Optional[str] = None
    type: Literal["video", "article", "thread", "tweet", "other"] = "video"
    stage: Literal["ideas", "scripting", "thumbnail", "filming", "editing", "published"] = (
        "ideas"
    )
    tags: list[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high"] = "medium"


class ContentUpdate(BaseModel):
    """Update content item request."""

    title: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[
        Literal["ideas", "scripting", "thumbnail", "filming", "editing", "published"]
    ] = None
    script: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    published_url: Optional[str] = None
    tags: Optional[list[str]] = None
    assigned_to: Optional[Literal["human", "agent"]] = None
    priority: Optional[Literal["low", "medium", "high"]] = None


class ContentPipelineResponse(BaseModel):
    """Response containing content pipeline state."""

    items: list[ContentItem]
    stats: dict = Field(default_factory=dict)


class GenerateScriptRequest(BaseModel):
    """Request to generate script for content item."""

    content_id: str
    instructions: Optional[str] = None


class GenerateScriptResponse(BaseModel):
    """Response from script generation."""

    content_id: str
    script: str
    success: bool
    message: Optional[str] = None
