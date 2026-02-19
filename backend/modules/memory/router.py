"""Memory module API endpoints."""

from fastapi import APIRouter, HTTPException, Query

from modules.activity.models import ActivityLogRequest
from modules.activity.service import activity_service

from .models import (
    DailyMemoryResponse,
    LongTermMemoryResponse,
    MemoryFilesResponse,
    MemoryStatsResponse,
    SearchResponse,
)
from .service import memory_service

router = APIRouter()


@router.get("/files", response_model=MemoryFilesResponse)
async def list_files():
    """List daily memory files with metadata."""
    files = memory_service.list_daily_files()
    return MemoryFilesResponse(files=files, total=len(files))


@router.get("/files/{date}", response_model=DailyMemoryResponse)
async def get_daily(date: str):
    """Get full daily memory content and parsed sections."""
    result = memory_service.get_daily(date)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No memory file for {date}")
    content, sections = result
    return DailyMemoryResponse(
        date=date,
        filename=f"{date}.md",
        content=content,
        sections=sections,
    )


@router.get("/long-term", response_model=LongTermMemoryResponse)
async def get_long_term():
    """Get MEMORY.md content and sections."""
    result = memory_service.get_long_term()
    if result is None:
        return LongTermMemoryResponse(content="", sections=[], exists=False)
    content, sections = result
    return LongTermMemoryResponse(content=content, sections=sections, exists=True)


@router.get("/search", response_model=SearchResponse)
async def search(q: str = Query(..., min_length=2)):
    """Case-insensitive full-text search across all memory files."""
    hits = memory_service.search(q)
    await activity_service.log_event(ActivityLogRequest(
        actor="user", action="memory.searched", resource_type="memory",
        resource_name=q, module="memory",
        details={"hits": len(hits)},
    ))
    return SearchResponse(query=q, hits=hits, total=len(hits))


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_stats():
    """Lightweight stats for overview widget."""
    stats = memory_service.get_stats()
    return MemoryStatsResponse(**stats)
