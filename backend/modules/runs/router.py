"""Agent Runs API router."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from core.config import settings
from modules.activity.models import ActivityLogRequest
from modules.activity.service import activity_service

from .models import AgentRun, AgentRunCreate, AgentRunList, HeatmapDay
from .service import runs_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth dependency for ingest
# ---------------------------------------------------------------------------


async def verify_mc_token(x_mc_token: str = Header(...)):
    """Validate the X-MC-Token header against settings."""
    if x_mc_token != settings.openclaw_hooks_token:
        raise HTTPException(status_code=403, detail="Invalid token")


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------


@router.post("/ingest", response_model=AgentRun, status_code=201)
async def ingest_run(
    payload: AgentRunCreate,
    _: None = Depends(verify_mc_token),
) -> AgentRun:
    """Ingest a new agent run record. Requires X-MC-Token auth."""
    run = await runs_service.ingest(payload)

    # Log to activity feed
    try:
        await activity_service.log_event(
            ActivityLogRequest(
                actor=payload.agent_id,
                action="agent.run.completed",
                resource_type="agent_run",
                resource_id=str(run.id),
                resource_name=f"{payload.agent_id}/{payload.run_type}",
                details={
                    "trigger": payload.trigger,
                    "outcome": payload.outcome or payload.status,
                    "duration_ms": payload.duration_ms,
                    "tokens_used": payload.tokens_used,
                    "channel": payload.channel,
                },
                module="runs",
            )
        )
    except Exception:
        logger.warning("Failed to log activity for run %s", run.id, exc_info=True)

    return run


# ---------------------------------------------------------------------------
# List / search
# ---------------------------------------------------------------------------


@router.get("/", response_model=AgentRunList)
async def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    agent_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    outcome: str | None = Query(None),
    trigger: str | None = Query(None),
) -> AgentRunList:
    """Paginated list of agent runs with optional filters."""
    return await runs_service.list_runs(
        page=page,
        page_size=page_size,
        agent_id=agent_id,
        date_from=date_from,
        date_to=date_to,
        outcome=outcome,
        trigger=trigger,
    )


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------


@router.get("/heatmap", response_model=list[HeatmapDay])
async def get_heatmap(
    year: int = Query(default=None),
) -> list[HeatmapDay]:
    """Daily run counts for the heatmap visualisation."""
    if year is None:
        year = datetime.now(timezone.utc).year
    return await runs_service.get_heatmap(year)


# ---------------------------------------------------------------------------
# Day detail
# ---------------------------------------------------------------------------


@router.get("/day", response_model=list[AgentRun])
async def get_day_runs(
    date: str = Query(..., description="YYYY-MM-DD"),
    agent_id: str | None = Query(None),
) -> list[AgentRun]:
    """All runs for a specific day."""
    return await runs_service.get_day_runs(date, agent_id)


# ---------------------------------------------------------------------------
# Agent timeline
# ---------------------------------------------------------------------------


@router.get("/agent/{agent_id}/timeline", response_model=AgentRunList)
async def get_agent_timeline(
    agent_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> AgentRunList:
    """Paginated run history for a single agent."""
    return await runs_service.get_agent_timeline(agent_id, page, page_size)


# ---------------------------------------------------------------------------
# Single run detail
# ---------------------------------------------------------------------------


@router.get("/{run_id}", response_model=AgentRun)
async def get_run(run_id: UUID) -> AgentRun:
    """Fetch a single run by ID."""
    run = await runs_service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
