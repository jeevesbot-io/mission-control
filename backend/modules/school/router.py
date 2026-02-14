"""School module API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

from .models import (
    CalendarEventsResponse,
    SchoolEmailsResponse,
    SchoolEventsResponse,
    SchoolStatsResponse,
    TodoistTasksResponse,
)
from .service import school_service

router = APIRouter()


@router.get("/calendar", response_model=CalendarEventsResponse)
async def list_calendar_events(
    days: int = Query(7, ge=1, le=30),
):
    """Family calendar events from Google Calendar (next N days)."""
    return await school_service.get_calendar_events(days=days)


@router.get("/events", response_model=SchoolEventsResponse)
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Upcoming school events from Matron's email processing."""
    events = await school_service.get_events(db, limit=limit)
    return SchoolEventsResponse(events=events, total=len(events))


@router.get("/emails", response_model=SchoolEmailsResponse)
async def list_emails(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Recent school emails."""
    emails = await school_service.get_emails(db, limit=limit)
    return SchoolEmailsResponse(emails=emails, total=len(emails))


@router.get("/tasks", response_model=TodoistTasksResponse)
async def list_tasks(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Todoist tasks and action items."""
    tasks = await school_service.get_tasks(db, limit=limit)
    return TodoistTasksResponse(tasks=tasks, total=len(tasks))


@router.get("/stats", response_model=SchoolStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Counts and summaries for overview."""
    return await school_service.get_stats(db)
