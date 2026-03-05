"""Overview module API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

from .models import OverviewResponse, StandupResponse
from .service import overview_service

router = APIRouter()


@router.get("/", response_model=OverviewResponse)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Get the full overview dashboard data."""
    return await overview_service.get_overview(db)


@router.get("/standup", response_model=StandupResponse)
async def get_standup(db: AsyncSession = Depends(get_db)):
    """Get the daily standup summary: task queue, activity, blockers, events."""
    return await overview_service.get_standup(db)
