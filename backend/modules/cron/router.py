"""Cron Monitor module router — FastAPI endpoints."""

from fastapi import APIRouter

from . import service
from .models import ChannelLoad, CronHealthSummary, CronJob

router = APIRouter()


@router.get("/schedule", response_model=list[CronJob])
async def list_cron_jobs():
    """Return all cron jobs with computed health status."""
    return await service.list_jobs()


@router.get("/health", response_model=CronHealthSummary)
async def get_health_summary():
    """Return aggregate health counts (ok / late / failing / never)."""
    return await service.get_health_summary()


@router.get("/channels", response_model=list[ChannelLoad])
async def list_channel_load():
    """Return estimated daily message load grouped by delivery channel."""
    return await service.list_channel_load()
