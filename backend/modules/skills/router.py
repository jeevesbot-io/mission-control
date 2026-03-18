"""Skills module API routes."""

import asyncio
import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.rate_limit import limiter

from .indexer import run_reindex
from .models import DriftEntry, ReindexRequest, ReindexResult, SkillDetail, SkillStats, SkillSummary
from .service import skills_browser_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[SkillSummary])
async def list_skills(
    source: str | None = Query(None, description="Filter by source label"),
    q: str | None = Query(None, description="Search name/description"),
    drifted: bool = Query(False, description="Show only drifted skills"),
    db: AsyncSession = Depends(get_db),
):
    """List all installed skills with metadata. Serves from DB if indexed, falls back to filesystem."""
    # Try DB first
    db_skills = await skills_browser_service.list_from_db(db, source=source, q=q, drifted=drifted)
    if db_skills:
        return db_skills

    # Fallback to filesystem scan (backwards compatible)
    skills = await asyncio.to_thread(skills_browser_service.scan_all)
    # Apply client-side filters for filesystem fallback
    if source:
        skills = [s for s in skills if s["source"] == source]
    if q:
        ql = q.lower()
        skills = [s for s in skills if ql in s["name"].lower() or ql in s["description"].lower()]
    return skills


# --- Static path routes BEFORE the /{skill_name} catch-all ---


@router.get("/drift", response_model=list[DriftEntry])
async def get_drift_report(
    since: datetime.datetime | None = Query(
        None, description="ISO datetime; defaults to 7 days ago"
    ),
    limit: int = Query(50, ge=1, le=500, description="Max entries to return"),
    db: AsyncSession = Depends(get_db),
):
    """Drift report — recent changes across all skills."""
    entries = await skills_browser_service.get_drift_report(db, since=since, limit=limit)
    return entries


@router.get("/stats", response_model=SkillStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    """Overview stats for the Skills Hub."""
    stats = await skills_browser_service.get_stats(db)
    return stats


@router.get("/{skill_name}", response_model=SkillDetail)
async def get_skill(
    skill_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get SKILL.md content for a specific skill, enriched with DB data."""
    content = await asyncio.to_thread(skills_browser_service.get_skill_content, skill_name)
    if content is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Enrich with DB data if available
    db_data = await skills_browser_service.get_skill_detail_from_db(db, skill_name)
    extra = db_data or {}

    return {
        "name": skill_name,
        "content": content,
        "source_label": extra.get("source_label"),
        "sha256_hash": extra.get("sha256_hash"),
        "last_changed_at": extra.get("last_changed_at"),
    }


@router.post("/reindex", response_model=ReindexResult)
@limiter.limit("1/minute")
async def reindex_skills(
    request: Request,
    body: ReindexRequest = ReindexRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a full re-index of all skill directories."""
    result = await run_reindex(db, source=body.source)
    return result
