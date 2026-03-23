"""Workspace module router — FastAPI endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from modules.activity.models import ActivityLogRequest
from modules.activity.service import activity_service

from . import service
from .models import (
    HeartbeatResponse,
    HistoryEntry,
    ModelResponse,
    SoulTemplate,
    UsageResponse,
    WorkspaceFileResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------


@router.get("/heartbeat", response_model=HeartbeatResponse)
async def get_heartbeat():
    return await service.get_heartbeat()


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def record_heartbeat():
    hb = await service.record_heartbeat()
    from core.websocket import manager

    await manager.broadcast("workspace:heartbeat", hb.model_dump(mode="json"))
    return hb


# ---------------------------------------------------------------------------
# Usage / Models
# ---------------------------------------------------------------------------


@router.get("/usage", response_model=UsageResponse)
async def get_usage():
    return await service.get_usage()


@router.get("/models", response_model=list[str])
async def get_models():
    return await service.get_models()


class _ModelSwitchBody(BaseModel):
    model: str


@router.post("/model", response_model=ModelResponse)
async def set_model(payload: _ModelSwitchBody):
    result = await service.set_model(payload.model)
    await activity_service.log_event(
        ActivityLogRequest(
            actor="user",
            action="model.switched",
            resource_type="model",
            resource_name=payload.model,
            module="workspace",
        )
    )
    return result


# ---------------------------------------------------------------------------
# Workspace files
# ---------------------------------------------------------------------------


@router.get("/workspace-file", response_model=WorkspaceFileResponse)
async def get_workspace_file(name: str = Query(...)):
    if not service.validate_workspace_filename(name):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Allowed: SOUL.md, IDENTITY.md, USER.md, AGENTS.md",
        )
    return await service.get_workspace_file(name)


class _WorkspaceFileBody(BaseModel):
    content: str


@router.put("/workspace-file")
async def update_workspace_file(name: str = Query(...), payload: _WorkspaceFileBody = ...):
    if not service.validate_workspace_filename(name):
        raise HTTPException(status_code=400, detail="Invalid filename")
    await service.update_workspace_file(name, payload.content)
    await activity_service.log_event(
        ActivityLogRequest(
            actor="user",
            action="soul.updated",
            resource_type="soul",
            resource_name=name,
            module="workspace",
        )
    )
    return {"ok": True}


@router.get("/workspace-file/history", response_model=list[HistoryEntry])
async def get_workspace_file_history(name: str = Query(...)):
    if not service.validate_workspace_filename(name):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return await service.get_file_history(name)


class _RevertBody(BaseModel):
    index: int


@router.post("/workspace-file/revert")
async def revert_workspace_file(name: str = Query(...), payload: _RevertBody = ...):
    if not service.validate_workspace_filename(name):
        raise HTTPException(status_code=400, detail="Invalid filename")
    result = await service.revert_workspace_file(name, payload.index)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid history index")
    return result


# ---------------------------------------------------------------------------
# Soul templates
# ---------------------------------------------------------------------------


@router.get("/soul/templates", response_model=list[SoulTemplate])
async def get_soul_templates():
    return service.get_soul_templates()
