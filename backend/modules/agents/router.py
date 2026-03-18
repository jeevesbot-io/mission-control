"""Agents module API endpoints."""

import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.rate_limit import limiter
from core.websocket import manager

from .models import (
    AgentDetailResponse,
    AgentInfo,
    AgentLogEntry,
    AgentLogPage,
    AgentStatsResponse,
    CronResponse,
    LiveSession,
    OfficeViewResponse,
    TriggerResponse,
)
from modules.activity.models import ActivityLogRequest
from modules.activity.service import activity_service

from .service import agent_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[AgentInfo])
async def list_agents(db: AsyncSession = Depends(get_db)):
    """List known agents with activity summary."""
    return await agent_service.list_agents(db)


@router.get("/detailed", response_model=list[AgentDetailResponse])
async def list_agents_detailed(db: AsyncSession = Depends(get_db)):
    """List agents with rich metadata, status, and task counts."""
    return await agent_service.list_agents_detailed(db)


@router.get("/stats", response_model=AgentStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats: total entries, health rate, 24h count."""
    return await agent_service.get_stats(db)


@router.get("/cron", response_model=CronResponse)
async def get_cron():
    """Fetch cron schedule from OpenClaw gateway."""
    jobs = await agent_service.get_cron_jobs()
    return CronResponse(jobs=jobs)


@router.get("/sessions", response_model=list[LiveSession])
async def get_live_sessions():
    """Fetch live agent sessions from OpenClaw gateway."""
    return await agent_service.get_live_sessions()


@router.get("/office", response_model=OfficeViewResponse)
async def get_office_view(db: AsyncSession = Depends(get_db)):
    """Get the office view with agent workstations."""
    return await agent_service.get_office_view(db)


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


async def verify_mc_token(x_mc_token: str = Header(...)):
    """Validate the X-MC-Token header against settings."""
    if x_mc_token != settings.openclaw_hooks_token:
        raise HTTPException(status_code=403, detail="Invalid token")


class AgentLogCreateRequest(BaseModel):
    level: str = "info"
    message: str
    metadata: Optional[dict] = None


@router.post("/{agent_id}/log", response_model=AgentLogEntry, status_code=201)
async def create_agent_log(
    agent_id: str,
    body: AgentLogCreateRequest,
    _: None = Depends(verify_mc_token),
    db: AsyncSession = Depends(get_db),
):
    """Write a log entry for a specific agent. Requires X-MC-Token auth."""
    result = await db.execute(
        text("""
            INSERT INTO agent_log (agent, level, message, metadata, created_at)
            VALUES (:agent, :level, :message, CAST(:metadata AS jsonb), NOW())
            RETURNING id, agent, level, message, metadata, created_at
        """),
        {
            "agent": agent_id,
            "level": body.level,
            "message": body.message,
            "metadata": json.dumps(body.metadata) if body.metadata is not None else None,
        },
    )
    await db.commit()
    row = result.fetchone()
    return AgentLogEntry(
        id=row.id,
        agent_id=row.agent,
        level=row.level.lower(),
        message=row.message,
        metadata=row.metadata,
        created_at=row.created_at,
    )


class TriggerRequest(BaseModel):
    message: str = ""


@router.post("/{agent_id}/trigger", response_model=TriggerResponse)
@limiter.limit("5/minute")
async def trigger_agent(request: Request, agent_id: str, body: TriggerRequest = TriggerRequest()):
    """Trigger agent via OpenClaw gateway with optional prompt message."""
    success, message = await agent_service.trigger_agent(agent_id, body.message)
    if not success:
        raise HTTPException(status_code=502, detail=message)

    await manager.broadcast(
        "agents:activity",
        {"event": "trigger", "agent_id": agent_id, "message": message},
    )

    await activity_service.log_event(
        ActivityLogRequest(
            actor="user",
            action="agent.triggered",
            resource_type="agent",
            resource_id=agent_id,
            resource_name=agent_id,
            module="agents",
        )
    )

    return TriggerResponse(success=True, message=message, agent_id=agent_id)
