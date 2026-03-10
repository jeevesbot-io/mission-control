"""Skills browser API routes."""

import asyncio

from fastapi import APIRouter, HTTPException

from .models import SkillDetail, SkillSummary
from .service import skills_browser_service

router = APIRouter()


@router.get("/", response_model=list[SkillSummary])
async def list_skills():
    """List all installed skills with metadata."""
    skills = await asyncio.to_thread(skills_browser_service.scan_all)
    return skills


@router.get("/{skill_name}", response_model=SkillDetail)
async def get_skill(skill_name: str):
    """Get SKILL.md content for a specific skill."""
    content = await asyncio.to_thread(skills_browser_service.get_skill_content, skill_name)
    if content is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"name": skill_name, "content": content}
