"""Calendar module API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from .models import CalendarResponse, CronJobsResponse
from .service import calendar_service

router = APIRouter()


@router.get("/", response_model=CalendarResponse)
async def get_calendar(
    start_date: Optional[datetime] = Query(None, description="Start date for calendar view"),
    days_ahead: int = Query(14, description="Number of days to look ahead"),
):
    """Get the full calendar with cron jobs and scheduled tasks."""
    return await calendar_service.get_calendar(start_date, days_ahead)


@router.get("/jobs", response_model=CronJobsResponse)
async def get_cron_jobs():
    """Get all cron jobs from OpenClaw gateway."""
    jobs = await calendar_service.get_cron_jobs()
    return CronJobsResponse(jobs=jobs, total=len(jobs))
