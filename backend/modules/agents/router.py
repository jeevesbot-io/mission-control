"""Agents module API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.rate_limit import limiter
from core.websocket import manager

from .models import (
    AgentInfo,
    AgentLogPage,
    AgentStatsResponse,
    CronResponse,
    TriggerResponse,
)
from modules.activity.models import ActivityLogRequest
from modules.activity.service import activity_service

from .service import agent_service

router = APIRouter()


@router.get("/", response_model=list[AgentInfo])
async def list_agents(db: AsyncSession = Depends(get_db)):
    """List known agents with activity summary."""
    return await agent_service.list_agents(db)


@router.get("/stats", response_model=AgentStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats: total entries, health rate, 24h count."""
    return await agent_service.get_stats(db)


@router.get("/cron", response_model=CronResponse)
async def get_cron():
    """Fetch cron schedule from OpenClaw gateway."""
    jobs = await agent_service.get_cron_jobs()
    return CronResponse(jobs=jobs)


@router.get("/{agent_id}/log", response_model=AgentLogPage)
async def get_agent_log(
    agent_id: str,
    level: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Paginated log history for a specific agent."""
    entries, total = await agent_service.get_log(
        db, agent_id=agent_id, level=level, page=page, page_size=page_size
    )
    return AgentLogPage(entries=entries, total=total, page=page, page_size=page_size)


@router.post("/{agent_id}/trigger", response_model=TriggerResponse)
@limiter.limit("5/minute")
async def trigger_agent(request: Request, agent_id: str):
    """Trigger agent via OpenClaw gateway."""
    success, message = await agent_service.trigger_agent(agent_id)
    if not success:
        raise HTTPException(status_code=502, detail=message)

    await manager.broadcast(
        "agents:activity",
        {"event": "trigger", "agent_id": agent_id, "message": message},
    )

    await activity_service.log_event(ActivityLogRequest(
        actor="user", action="agent.triggered", resource_type="agent",
        resource_id=agent_id, resource_name=agent_id, module="agents",
    ))

    return TriggerResponse(success=True, message=message, agent_id=agent_id)
