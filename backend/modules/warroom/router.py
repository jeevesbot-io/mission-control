"""War Room API router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .models import (
    CalendarDay,
    HeartbeatResponse,
    HistoryEntry,
    ModelResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithCount,
    Reference,
    ReferenceCreate,
    Skill,
    SkillCreate,
    SoulTemplate,
    Task,
    TaskComplete,
    TaskCreate,
    TaskUpdate,
    UsageResponse,
    WarRoomStats,
    WorkspaceFileResponse,
)
from .service import warroom_service

router = APIRouter()

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@router.get("/tasks", response_model=list[Task])
async def list_tasks(
    project: str | None = Query(None),
    priority: str | None = Query(None),
    tags: str | None = Query(None),
    status: str | None = Query(None),
) -> list[Task]:
    return await warroom_service.list_tasks(project=project, priority=priority, tags=tags, status=status)


@router.post("/tasks", response_model=Task)
async def create_task(payload: TaskCreate) -> Task:
    return await warroom_service.create_task(payload)


@router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, payload: TaskUpdate) -> Task:
    task = await warroom_service.update_task(task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str) -> dict:
    ok = await warroom_service.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str) -> dict:
    task = await warroom_service.run_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True, "message": "Task queued for execution"}


@router.get("/tasks/queue", response_model=list[Task])
async def get_queue() -> list[Task]:
    return await warroom_service.get_queue()


@router.post("/tasks/{task_id}/pickup", response_model=Task)
async def pickup_task(task_id: str) -> Task:
    task = await warroom_service.pickup_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/complete", response_model=Task)
async def complete_task(task_id: str, payload: TaskComplete = TaskComplete()) -> Task:
    task = await warroom_service.complete_task(task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------

@router.get("/tasks/{task_id}/references", response_model=list[Reference])
async def list_references(task_id: str) -> list[Reference]:
    refs = await warroom_service.list_references(task_id)
    if refs is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return refs


@router.post("/tasks/{task_id}/references", response_model=Reference)
async def add_reference(task_id: str, payload: ReferenceCreate) -> Reference:
    ref = await warroom_service.add_reference(task_id, payload)
    if ref is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return ref


@router.delete("/tasks/{task_id}/references/{ref_id}")
async def delete_reference(task_id: str, ref_id: str) -> dict:
    ok = await warroom_service.delete_reference(task_id, ref_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Reference not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@router.get("/projects", response_model=list[ProjectWithCount])
async def list_projects() -> list[ProjectWithCount]:
    return await warroom_service.list_projects()


@router.post("/projects", response_model=ProjectWithCount)
async def create_project(payload: ProjectCreate) -> ProjectWithCount:
    proj = await warroom_service.create_project(payload)
    from .models import ProjectWithCount
    return ProjectWithCount(**proj.model_dump(), task_count=0)


@router.put("/projects/{project_id}", response_model=ProjectWithCount)
async def update_project(project_id: str, payload: ProjectUpdate) -> ProjectWithCount:
    proj = await warroom_service.update_project(project_id, payload)
    if proj is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectWithCount(**proj.model_dump(), task_count=0)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str) -> dict:
    ok, error = await warroom_service.delete_project(project_id)
    if not ok:
        if error and "Cannot delete" in error:
            raise HTTPException(status_code=422, detail=error)
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@router.get("/tags", response_model=list[str])
async def list_tags() -> list[str]:
    return await warroom_service.list_tags()


# ---------------------------------------------------------------------------
# Usage / Models
# ---------------------------------------------------------------------------

@router.get("/usage", response_model=UsageResponse)
async def get_usage() -> UsageResponse:
    return await warroom_service.get_usage()


@router.get("/models", response_model=list[str])
async def get_models() -> list[str]:
    return await warroom_service.get_models()


class ModelSwitchRequest(ModelResponse):
    model: str


from pydantic import BaseModel as _BaseModel


class _ModelSwitchBody(_BaseModel):
    model: str


@router.post("/model", response_model=ModelResponse)
async def set_model(payload: _ModelSwitchBody) -> ModelResponse:
    return await warroom_service.set_model(payload.model)


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

@router.get("/heartbeat", response_model=HeartbeatResponse)
async def get_heartbeat() -> HeartbeatResponse:
    return await warroom_service.get_heartbeat()


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def record_heartbeat() -> HeartbeatResponse:
    return await warroom_service.record_heartbeat()


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

@router.get("/skills", response_model=list[Skill])
async def list_skills() -> list[Skill]:
    return await warroom_service.list_skills()


@router.post("/skills", response_model=Skill)
async def create_skill(payload: SkillCreate) -> Skill:
    return await warroom_service.create_skill(payload)


@router.get("/skills/{skill_id}/content")
async def get_skill_content(skill_id: str) -> dict:
    content = await warroom_service.get_skill_content(skill_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"content": content}


class _ToggleBody(_BaseModel):
    enabled: bool | None = None


@router.post("/skills/{skill_id}/toggle", response_model=Skill)
async def toggle_skill(skill_id: str, payload: _ToggleBody = _ToggleBody()) -> Skill:
    skill = await warroom_service.toggle_skill(skill_id, payload.enabled)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str) -> dict:
    ok, error = await warroom_service.delete_skill(skill_id)
    if not ok:
        if error and "Can only delete" in error:
            raise HTTPException(status_code=422, detail=error)
        raise HTTPException(status_code=404, detail=error or "Skill not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Workspace files (SOUL.md, IDENTITY.md, USER.md, AGENTS.md)
# ---------------------------------------------------------------------------

@router.get("/workspace-file", response_model=WorkspaceFileResponse)
async def get_workspace_file(name: str = Query(...)) -> WorkspaceFileResponse:
    if not warroom_service._validate_workspace_filename(name):
        raise HTTPException(status_code=400, detail=f"Invalid filename. Allowed: SOUL.md, IDENTITY.md, USER.md, AGENTS.md")
    return await warroom_service.get_workspace_file(name)


class _WorkspaceFileBody(_BaseModel):
    content: str


@router.put("/workspace-file")
async def update_workspace_file(name: str = Query(...), payload: _WorkspaceFileBody = ...) -> dict:
    if not warroom_service._validate_workspace_filename(name):
        raise HTTPException(status_code=400, detail="Invalid filename")
    await warroom_service.update_workspace_file(name, payload.content)
    return {"ok": True}


@router.get("/workspace-file/history", response_model=list[HistoryEntry])
async def get_workspace_file_history(name: str = Query(...)) -> list[HistoryEntry]:
    if not warroom_service._validate_workspace_filename(name):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return await warroom_service.get_file_history(name)


class _RevertBody(_BaseModel):
    index: int


@router.post("/workspace-file/revert")
async def revert_workspace_file(name: str = Query(...), payload: _RevertBody = ...) -> WorkspaceFileResponse:
    if not warroom_service._validate_workspace_filename(name):
        raise HTTPException(status_code=400, detail="Invalid filename")
    result = await warroom_service.revert_workspace_file(name, payload.index)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid history index")
    return result


@router.get("/soul/templates", response_model=list[SoulTemplate])
async def get_soul_templates() -> list[SoulTemplate]:
    return warroom_service.get_soul_templates()


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

@router.get("/calendar")
async def get_calendar() -> dict[str, CalendarDay]:
    return await warroom_service.get_calendar()


# ---------------------------------------------------------------------------
# Stats (overview widget)
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=WarRoomStats)
async def get_stats() -> WarRoomStats:
    return await warroom_service.get_stats()
