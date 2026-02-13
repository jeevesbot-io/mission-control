"""Agents module API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.websocket import manager

from .models import (
    AgentInfo,
    AgentRunsPage,
    AgentStatsResponse,
    CronResponse,
    TriggerResponse,
)
from .service import agent_service

router = APIRouter()


@router.get("/", response_model=list[AgentInfo])
async def list_agents(db: AsyncSession = Depends(get_db)):
    """List known agents with last run info."""
    return await agent_service.list_agents(db)


@router.get("/stats", response_model=AgentStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats: total runs, success rate, 24h count."""
    return await agent_service.get_stats(db)


@router.get("/cron", response_model=CronResponse)
async def get_cron():
    """Fetch cron schedule from OpenClaw gateway."""
    jobs = await agent_service.get_cron_jobs()
    return CronResponse(jobs=jobs)


@router.get("/{agent_id}/runs", response_model=AgentRunsPage)
async def get_agent_runs(
    agent_id: str,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Paginated run history for a specific agent."""
    runs, total = await agent_service.get_runs(
        db, agent_id=agent_id, status=status, page=page, page_size=page_size
    )
    return AgentRunsPage(runs=runs, total=total, page=page, page_size=page_size)


@router.post("/{agent_id}/trigger", response_model=TriggerResponse)
async def trigger_agent(agent_id: str):
    """Trigger agent via OpenClaw gateway."""
    success, message = await agent_service.trigger_agent(agent_id)
    if not success:
        raise HTTPException(status_code=502, detail=message)

    # Broadcast trigger event on WebSocket
    await manager.broadcast(
        "agents:activity",
        {"event": "trigger", "agent_id": agent_id, "message": message},
    )

    return TriggerResponse(success=True, message=message, agent_id=agent_id)
