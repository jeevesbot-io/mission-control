"""Tasks API router — Postgres-backed replacement for warroom task endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.websocket import manager
from modules.activity.models import ActivityLogRequest
from modules.activity.service import activity_service

from . import service
from .models import ActivityEntry, Comment, CommentCreate, Task, TaskComplete, TaskCreate, TaskStats, TaskUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Tasks CRUD
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[Task])
async def list_tasks(
    project: str | None = Query(None),
    priority: str | None = Query(None),
    tags: str | None = Query(None),
    status: str | None = Query(None),
) -> list[Task]:
    return await service.list_tasks(
        project=project, priority=priority, tags=tags, status=status
    )


@router.post("/", response_model=Task)
async def create_task(payload: TaskCreate) -> Task:
    try:
        task = await service.create_task(payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    await activity_service.log_event(
        ActivityLogRequest(
            actor="user",
            action="task.created",
            resource_type="task",
            resource_id=task.id,
            resource_name=task.title,
            module="tasks",
        )
    )
    await manager.broadcast("tasks:task:created", task.model_dump(mode="json"))
    return task


@router.get("/queue", response_model=list[Task])
async def get_queue() -> list[Task]:
    return await service.get_queue()


@router.get("/tags", response_model=list[str])
async def list_tags() -> list[str]:
    return await service.list_tags()


@router.get("/stats", response_model=TaskStats)
async def get_stats() -> TaskStats:
    return await service.get_stats()


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: int) -> Task:
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: int, payload: TaskUpdate) -> Task:
    try:
        task = await service.update_task(task_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await activity_service.log_event(
        ActivityLogRequest(
            actor="user",
            action="task.updated",
            resource_type="task",
            resource_id=task.id,
            resource_name=task.title,
            module="tasks",
        )
    )
    await manager.broadcast("tasks:task:updated", task.model_dump(mode="json"))
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: int) -> dict:
    ok = await service.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    await activity_service.log_event(
        ActivityLogRequest(
            actor="user",
            action="task.deleted",
            resource_type="task",
            resource_id=str(task_id),
            module="tasks",
        )
    )
    await manager.broadcast("tasks:task:deleted", {"id": str(task_id)})
    return {"ok": True}


@router.post("/{task_id}/run")
async def run_task(task_id: int) -> dict:
    task = await service.run_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await manager.broadcast("tasks:task:updated", task.model_dump(mode="json"))
    return {"ok": True, "message": "Task queued for execution"}


@router.post("/{task_id}/pickup", response_model=Task)
async def pickup_task(task_id: int) -> Task:
    task = await service.pickup_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await manager.broadcast("tasks:task:updated", task.model_dump(mode="json"))
    return task


@router.post("/{task_id}/complete", response_model=Task)
async def complete_task(task_id: int, payload: TaskComplete = TaskComplete()) -> Task:
    task = await service.complete_task(task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await activity_service.log_event(
        ActivityLogRequest(
            actor="system",
            action="task.completed",
            resource_type="task",
            resource_id=task.id,
            resource_name=task.title,
            module="tasks",
        )
    )
    await manager.broadcast("tasks:task:updated", task.model_dump(mode="json"))
    return task


# ---------------------------------------------------------------------------
# Atomic task checkout (claim / release)
# ---------------------------------------------------------------------------


class _ClaimBody(BaseModel):
    agent_id: str


@router.post("/{task_id}/claim", response_model=Task)
async def claim_task(task_id: int, payload: _ClaimBody) -> Task:
    try:
        task = await service.claim_task(task_id, payload.agent_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await manager.broadcast("tasks:task:claimed", task.model_dump(mode="json"))
    return task


@router.post("/{task_id}/release", response_model=Task)
async def release_task(task_id: int) -> Task:
    task = await service.release_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found or not claimed")
    await manager.broadcast("tasks:task:released", task.model_dump(mode="json"))
    return task


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@router.get("/{task_id}/comments", response_model=list[Comment])
async def list_comments(task_id: int):
    return await service.list_comments(task_id)


@router.post("/{task_id}/comments", response_model=Comment, status_code=201)
async def create_comment(task_id: int, payload: CommentCreate):
    comment = await service.create_comment(task_id, payload)
    await manager.broadcast("tasks:comment:created", comment.model_dump(mode="json"))
    return comment


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int):
    ok = await service.delete_comment(comment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Comment not found")
    await manager.broadcast("tasks:comment:deleted", {"id": comment_id})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Activity feed for task
# ---------------------------------------------------------------------------


@router.get("/{task_id}/activity", response_model=list[ActivityEntry])
async def list_task_activity(task_id: int, limit: int = Query(50, ge=1, le=200)):
    return await service.list_task_activity(task_id, limit=limit)
