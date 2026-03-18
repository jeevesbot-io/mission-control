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
    ActivityEntry,
    Comment,
    CommentCreate,
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
        type=m.get("type") or "feature",
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
        proof=m.get("proof"),
        pickedUp=bool(m.get("picked_up")),
        claimedBy=m.get("claimed_by"),
        claimedAt=_iso_or_none(m.get("claimed_at")),
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
                    type, tags, slug, project, schedule, scheduled_at,
                    blocked_by, estimated_hours
                ) VALUES (
                    :title, :description, :agent_id, :created_by, :state, :priority,
                    :type, :tags, :slug, :project, :schedule, :scheduled_at,
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
                "type": payload.type or "feature",
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
            elif key in ("title", "description", "project", "schedule", "result", "error", "type"):
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
    """Mark task as done with optional result/error. Proof required."""
    # Validate proof: at least one field must be provided
    proof = payload.proof
    if not proof or not any(proof.values()):
        raise ValueError(
            "Proof of work required to complete a task. "
            "Provide at least one of: pr_url, ci_status, test_output, files_changed"
        )

    async with async_session() as session:
        proof_json = json.dumps(proof) if proof else None
        result = await session.execute(
            text("""
                UPDATE mc_tasks
                SET state = 'done',
                    result = :result,
                    error = :error,
                    proof = CAST(:proof AS jsonb),
                    completed_at = now(),
                    updated_at = now()
                WHERE id = :id
                RETURNING *
            """),
            {
                "id": task_id,
                "result": payload.result,
                "error": payload.error,
                "proof": proof_json,
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


# ---------------------------------------------------------------------------
# Atomic task checkout (claim / release)
# ---------------------------------------------------------------------------


async def claim_task(task_id: int, agent_id: str) -> Task | None:
    """Atomically claim a task for an agent. Returns None if not found, raises ValueError if already claimed."""
    async with async_session() as session:
        # SELECT FOR UPDATE SKIP LOCKED — only returns the row if it's unclaimed and not locked
        result = await session.execute(
            text("""
                SELECT id FROM mc_tasks
                WHERE id = :id AND claimed_by IS NULL
                FOR UPDATE SKIP LOCKED
            """),
            {"id": task_id},
        )
        row = result.first()
        if row is None:
            # Either task doesn't exist or is already claimed/locked
            check = await session.execute(
                text("SELECT id, claimed_by FROM mc_tasks WHERE id = :id"),
                {"id": task_id},
            )
            existing = check.first()
            if existing is None:
                return None  # Task doesn't exist
            raise ValueError(f"Task already claimed by {existing._mapping['claimed_by']}")

        # Claim it
        update_result = await session.execute(
            text("""
                UPDATE mc_tasks
                SET claimed_by = :agent_id,
                    claimed_at = now(),
                    state = 'in_progress',
                    started_at = COALESCE(started_at, now()),
                    updated_at = now()
                WHERE id = :id
                RETURNING *
            """),
            {"id": task_id, "agent_id": agent_id},
        )
        updated = update_result.first()
        await session.commit()
        return _row_to_task(updated) if updated else None


async def release_task(task_id: int) -> Task | None:
    """Release a claimed task (on failure/timeout)."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                UPDATE mc_tasks
                SET claimed_by = NULL,
                    claimed_at = NULL,
                    state = 'todo',
                    updated_at = now()
                WHERE id = :id AND claimed_by IS NOT NULL
                RETURNING *
            """),
            {"id": task_id},
        )
        row = result.first()
        await session.commit()
        return _row_to_task(row) if row else None


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


async def list_comments(task_id: int) -> list[Comment]:
    """List all comments for a task, newest first."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT id, task_id, author_id, body, comment_type, created_at
                FROM mc_comments
                WHERE task_id = :task_id
                ORDER BY created_at DESC
            """),
            {"task_id": task_id},
        )
        return [
            Comment(
                id=r._mapping["id"],
                taskId=r._mapping["task_id"],
                authorId=r._mapping["author_id"],
                body=r._mapping["body"],
                commentType=r._mapping["comment_type"],
                createdAt=_iso_or_none(r._mapping["created_at"]) or "",
            )
            for r in result.all()
        ]


async def create_comment(task_id: int, payload: CommentCreate) -> Comment:
    """Create a comment on a task."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO mc_comments (task_id, author_id, body, comment_type)
                VALUES (:task_id, :author_id, :body, :comment_type)
                RETURNING id, task_id, author_id, body, comment_type, created_at
            """),
            {
                "task_id": task_id,
                "author_id": payload.authorId,
                "body": payload.body,
                "comment_type": payload.commentType,
            },
        )
        row = result.first()
        await session.commit()
        m = row._mapping
        return Comment(
            id=m["id"],
            taskId=m["task_id"],
            authorId=m["author_id"],
            body=m["body"],
            commentType=m["comment_type"],
            createdAt=_iso_or_none(m["created_at"]) or "",
        )


async def delete_comment(comment_id: int) -> bool:
    """Delete a comment by ID."""
    async with async_session() as session:
        result = await session.execute(
            text("DELETE FROM mc_comments WHERE id = :id"),
            {"id": comment_id},
        )
        await session.commit()
        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Task Activity Feed
# ---------------------------------------------------------------------------


async def list_task_activity(task_id: int, limit: int = 50) -> list[ActivityEntry]:
    """List activity entries for a task, newest first."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT id, task_id, agent_id, action, detail, created_at
                FROM mc_activity
                WHERE task_id = :task_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"task_id": task_id, "limit": limit},
        )
        return [
            ActivityEntry(
                id=r._mapping["id"],
                taskId=r._mapping["task_id"],
                agentId=r._mapping["agent_id"],
                action=r._mapping["action"],
                detail=r._mapping["detail"],
                createdAt=_iso_or_none(r._mapping["created_at"]) or "",
            )
            for r in result.all()
        ]
