"""Tasks service — Postgres-backed business logic for mc_tasks."""

from __future__ import annotations

import json
import logging
import re
import secrets
from datetime import datetime

from sqlalchemy import text

from core.database import async_session

from .models import (
    PRIORITY_INT_TO_STR,
    PRIORITY_STR_TO_INT,
    VALID_STATES,
    Task,
    TaskComplete,
    TaskCreate,
    TaskStats,
    TaskUpdate,
    state_to_status,
    status_to_state,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_slug(title: str, max_len: int = 50) -> str:
    """Generate a URL-friendly slug from a title."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_len]


def _ensure_list(val) -> list:
    """Normalise a value that may be a Postgres array, list, or None."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return list(val)


def _iso_or_none(dt) -> str | None:
    """Convert a datetime to ISO string, or return None."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _row_to_task(row) -> Task:
    """Convert a SQLAlchemy Row mapping to a Task API model."""
    m = row._mapping

    # Parse references_ (jsonb → list[dict])
    refs_raw = m.get("references_")
    if refs_raw is None:
        refs = []
    elif isinstance(refs_raw, str):
        try:
            refs = json.loads(refs_raw)
        except (json.JSONDecodeError, TypeError):
            refs = []
    else:
        refs = refs_raw

    # Convert blocked_by / blocks arrays — elements may be ints or strings
    blocked_by = [str(x) for x in _ensure_list(m.get("blocked_by"))]
    blocks = [str(x) for x in _ensure_list(m.get("blocks"))]

    priority_int = m.get("priority", 3)
    priority_str = PRIORITY_INT_TO_STR.get(priority_int, "medium")

    state = m.get("state", "backlog")
    status = state_to_status(state)

    return Task(
        id=str(m["id"]),
        title=m["title"],
        description=m.get("description") or "",
        status=status,
        priority=priority_str,
        project=m.get("project"),
        tags=_ensure_list(m.get("tags")),
        skill=m.get("agent_id") or None,
        schedule=m.get("schedule"),
        scheduledAt=_iso_or_none(m.get("scheduled_at")),
        references=refs,
        blockedBy=blocked_by,
        blocks=blocks,
        startedAt=_iso_or_none(m.get("started_at")),
        completedAt=_iso_or_none(m.get("completed_at")),
        result=m.get("result"),
        error=m.get("error"),
        pickedUp=bool(m.get("picked_up")),
        createdAt=_iso_or_none(m["created_at"]),
        updatedAt=_iso_or_none(m["updated_at"]),
        estimatedHours=m.get("estimated_hours"),
        actualHours=m.get("actual_hours"),
        slug=m.get("slug"),
    )


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


async def list_tasks(
    project: str | None = None,
    priority: str | None = None,
    tags: str | None = None,
    status: str | None = None,
) -> list[Task]:
    """List tasks with optional filters."""
    conditions: list[str] = []
    params: dict = {}

    if project:
        conditions.append("project = :project")
        params["project"] = project
    if priority:
        pri_int = PRIORITY_STR_TO_INT.get(priority)
        if pri_int is not None:
            conditions.append("priority = :priority")
            params["priority"] = pri_int
    if status:
        state = status_to_state(status)
        conditions.append("state = :state")
        params["state"] = state
    if tags:
        # tags query param is comma-separated
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            conditions.append("tags && :tags")
            params["tags"] = tag_list

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with async_session() as session:
        result = await session.execute(
            text(f"""
                SELECT * FROM mc_tasks
                {where}
                ORDER BY priority ASC, created_at DESC
            """),
            params,
        )
        return [_row_to_task(row) for row in result.all()]


async def get_task(task_id: int) -> Task | None:
    """Fetch a single task by integer ID."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM mc_tasks WHERE id = :id"),
            {"id": task_id},
        )
        row = result.first()
        return _row_to_task(row) if row else None


async def create_task(payload: TaskCreate) -> Task:
    """Create a new task and return it."""
    # Validate priority
    priority_int = PRIORITY_STR_TO_INT.get(payload.priority)
    if priority_int is None:
        raise ValueError(f"Invalid priority: {payload.priority}")

    # Validate state
    state = status_to_state(payload.status)
    if state not in VALID_STATES:
        raise ValueError(f"Invalid status: {payload.status}")

    # Generate slug
    slug = _generate_slug(payload.title)

    agent_id = payload.skill or ""

    # Convert blockedBy strings to text[] for Postgres
    blocked_by = payload.blockedBy or []

    # Convert scheduledAt string to timestamptz or None
    scheduled_at = None
    if payload.scheduledAt:
        try:
            scheduled_at = datetime.fromisoformat(payload.scheduledAt)
        except (ValueError, TypeError):
            scheduled_at = None

    async with async_session() as session:
        # Handle slug uniqueness — retry with random suffix on conflict
        for _attempt in range(5):
            check = await session.execute(
                text("SELECT id FROM mc_tasks WHERE slug = :slug"),
                {"slug": slug},
            )
            if check.first() is None:
                break
            slug = f"{_generate_slug(payload.title, max_len=42)}-{secrets.token_hex(3)}"

        result = await session.execute(
            text("""
                INSERT INTO mc_tasks (
                    title, description, agent_id, created_by, state, priority,
                    tags, slug, project, schedule, scheduled_at,
                    blocked_by, estimated_hours
                ) VALUES (
                    :title, :description, :agent_id, :created_by, :state, :priority,
                    :tags, :slug, :project, :schedule, :scheduled_at,
                    :blocked_by, :estimated_hours
                )
                RETURNING *
            """),
            {
                "title": payload.title,
                "description": payload.description or "",
                "agent_id": agent_id,
                "created_by": "user",
                "state": state,
                "priority": priority_int,
                "tags": payload.tags or [],
                "slug": slug,
                "project": payload.project,
                "schedule": payload.schedule,
                "scheduled_at": scheduled_at,
                "blocked_by": blocked_by,
                "estimated_hours": payload.estimatedHours,
            },
        )
        row = result.first()
        await session.commit()
        return _row_to_task(row)


async def update_task(task_id: int, payload: TaskUpdate) -> Task | None:
    """Update an existing task. Returns None if not found."""
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return await get_task(task_id)

    async with async_session() as session:
        # Check exists
        check = await session.execute(
            text("SELECT id FROM mc_tasks WHERE id = :id"),
            {"id": task_id},
        )
        if check.first() is None:
            return None

        set_parts: list[str] = []
        params: dict = {"id": task_id}

        for key, value in updates.items():
            if key == "priority":
                pri_int = PRIORITY_STR_TO_INT.get(value)
                if pri_int is None:
                    raise ValueError(f"Invalid priority: {value}")
                set_parts.append("priority = :priority")
                params["priority"] = pri_int
            elif key == "status":
                state = status_to_state(value)
                if state not in VALID_STATES:
                    raise ValueError(f"Invalid status: {value}")
                set_parts.append("state = :state")
                params["state"] = state
            elif key == "skill":
                set_parts.append("agent_id = :agent_id")
                params["agent_id"] = value or ""
            elif key == "scheduledAt":
                scheduled_at = None
                if value:
                    try:
                        scheduled_at = datetime.fromisoformat(value)
                    except (ValueError, TypeError):
                        scheduled_at = None
                set_parts.append("scheduled_at = :scheduled_at")
                params["scheduled_at"] = scheduled_at
            elif key == "startedAt":
                started_at = None
                if value:
                    try:
                        started_at = datetime.fromisoformat(value)
                    except (ValueError, TypeError):
                        started_at = None
                set_parts.append("started_at = :started_at")
                params["started_at"] = started_at
            elif key == "completedAt":
                completed_at = None
                if value:
                    try:
                        completed_at = datetime.fromisoformat(value)
                    except (ValueError, TypeError):
                        completed_at = None
                set_parts.append("completed_at = :completed_at")
                params["completed_at"] = completed_at
            elif key == "blockedBy":
                set_parts.append("blocked_by = :blocked_by")
                params["blocked_by"] = value or []
            elif key == "blocks":
                set_parts.append("blocks = :blocks")
                params["blocks"] = value or []
            elif key in ("tags",):
                set_parts.append("tags = :tags")
                params["tags"] = value or []
            elif key in ("title", "description", "project", "schedule", "result", "error"):
                set_parts.append(f"{key} = :{key}")
                params[key] = value
            elif key == "estimatedHours":
                set_parts.append("estimated_hours = :estimated_hours")
                params["estimated_hours"] = value
            elif key == "actualHours":
                set_parts.append("actual_hours = :actual_hours")
                params["actual_hours"] = value

        if not set_parts:
            return await get_task(task_id)

        set_parts.append("updated_at = now()")
        set_clause = ", ".join(set_parts)

        result = await session.execute(
            text(f"UPDATE mc_tasks SET {set_clause} WHERE id = :id RETURNING *"),
            params,
        )
        row = result.first()
        await session.commit()
        return _row_to_task(row) if row else None


async def delete_task(task_id: int) -> bool:
    """Delete a task. Returns True if deleted, False if not found."""
    async with async_session() as session:
        result = await session.execute(
            text("DELETE FROM mc_tasks WHERE id = :id"),
            {"id": task_id},
        )
        await session.commit()
        return result.rowcount > 0


async def run_task(task_id: int) -> Task | None:
    """Mark a task as in-progress (the /run endpoint)."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                UPDATE mc_tasks
                SET state = 'in_progress',
                    started_at = COALESCE(started_at, now()),
                    updated_at = now()
                WHERE id = :id
                RETURNING *
            """),
            {"id": task_id},
        )
        row = result.first()
        await session.commit()
        return _row_to_task(row) if row else None


# ---------------------------------------------------------------------------
# Agent queue protocol
# ---------------------------------------------------------------------------


async def get_queue() -> list[Task]:
    """Return pickup-eligible tasks: state=todo, not picked up, not blocked.

    Sorted by priority ASC (1=urgent first), then created_at ASC (oldest first).
    """
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT * FROM mc_tasks
                WHERE state = 'todo'
                  AND (picked_up IS NULL OR picked_up = false)
                  AND (blocked_by IS NULL OR blocked_by = '{}')
                ORDER BY priority ASC, created_at ASC
            """)
        )
        return [_row_to_task(row) for row in result.all()]


async def pickup_task(task_id: int) -> Task | None:
    """Agent picks up a task: set picked_up=true, state=in_progress, started_at=now()."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                UPDATE mc_tasks
                SET state = 'in_progress',
                    picked_up = true,
                    started_at = COALESCE(started_at, now()),
                    updated_at = now()
                WHERE id = :id
                RETURNING *
            """),
            {"id": task_id},
        )
        row = result.first()
        await session.commit()
        return _row_to_task(row) if row else None


async def complete_task(task_id: int, payload: TaskComplete) -> Task | None:
    """Mark task as done with optional result/error."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                UPDATE mc_tasks
                SET state = 'done',
                    result = :result,
                    error = :error,
                    completed_at = now(),
                    updated_at = now()
                WHERE id = :id
                RETURNING *
            """),
            {
                "id": task_id,
                "result": payload.result,
                "error": payload.error,
            },
        )
        row = result.first()
        await session.commit()
        return _row_to_task(row) if row else None


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


async def list_tags() -> list[str]:
    """Return all unique tags across all tasks, sorted."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT DISTINCT unnest(tags) AS tag
                FROM mc_tasks
                WHERE tags IS NOT NULL AND tags != '{}'
                ORDER BY tag
            """)
        )
        return [row._mapping["tag"] for row in result.all()]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def get_stats() -> TaskStats:
    """Return task stats for the overview widget."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT
                    COUNT(*) FILTER (WHERE state = 'in_progress') AS in_progress_count,
                    COUNT(*) FILTER (WHERE state = 'todo') AS todo_count
                FROM mc_tasks
            """)
        )
        row = result.first()
        m = row._mapping

        return TaskStats(
            in_progress_count=m["in_progress_count"] or 0,
            todo_count=m["todo_count"] or 0,
            last_heartbeat=None,
            active_model="unknown",
        )
