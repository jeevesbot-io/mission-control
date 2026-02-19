"""Activity Timeline API router."""

from __future__ import annotations

from fastapi import APIRouter, Query

from .models import ActivityFeedResponse, ActivityStats
from .service import activity_service

router = APIRouter()


@router.get("/feed", response_model=ActivityFeedResponse)
async def get_feed(
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    module: str | None = Query(None),
    actor: str | None = Query(None),
    action: str | None = Query(None),
) -> ActivityFeedResponse:
    """Paginated activity feed with optional filters."""
    return await activity_service.get_feed(
        limit=limit, cursor=cursor, module=module, actor=actor, action=action
    )


@router.get("/stats", response_model=ActivityStats)
async def get_stats() -> ActivityStats:
    """Activity statistics."""
    return await activity_service.get_stats()
