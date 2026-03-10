"""Projects API router."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .models import ProjectCreate, ProjectDetail, ProjectUpdate, ProjectWithCounts
from . import service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[ProjectWithCounts])
async def list_projects() -> list[ProjectWithCounts]:
    return await service.list_projects()


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str) -> ProjectDetail:
    project = await service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=ProjectWithCounts, status_code=201)
async def create_project(payload: ProjectCreate) -> ProjectWithCounts:
    try:
        return await service.create_project(payload)
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=422, detail=f"Project ID '{payload.id}' already exists")
        raise HTTPException(status_code=422, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectWithCounts)
async def update_project(project_id: str, payload: ProjectUpdate) -> ProjectWithCounts:
    result = await service.update_project(project_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@router.delete("/{project_id}")
async def delete_project(project_id: str) -> dict:
    ok, error = await service.delete_project(project_id)
    if not ok:
        if error and "Cannot delete" in error:
            raise HTTPException(status_code=422, detail=error)
        raise HTTPException(status_code=404, detail=error or "Project not found")
    return {"ok": True}
