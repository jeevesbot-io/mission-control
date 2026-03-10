"""Projects service — database operations for mc_projects."""

from __future__ import annotations

import json
import logging

from sqlalchemy import text

from core.database import async_session

from .models import (
    ProjectCreate,
    ProjectDetail,
    ProjectDoc,
    ProjectUpdate,
    ProjectWithCounts,
    TaskSummary,
)

logger = logging.getLogger(__name__)


def _parse_docs(raw) -> list[dict]:
    """Parse docs from DB — could be a JSON string or already a list."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    return raw


def _row_to_project_dict(row) -> dict:
    """Convert a DB row mapping to a project dict."""
    m = dict(row._mapping)
    m["docs"] = [ProjectDoc(**d) for d in _parse_docs(m.get("docs"))]
    return m


async def list_projects() -> list[ProjectWithCounts]:
    async with async_session() as session:
        result = await session.execute(
            text("""
            SELECT p.*,
                   COALESCE(tc.task_count, 0) AS task_count,
                   COALESCE(tc.agent_count, 0) AS agent_count
            FROM mc_projects p
            LEFT JOIN (
                SELECT project,
                       COUNT(*) AS task_count,
                       COUNT(DISTINCT agent_id) FILTER (WHERE agent_id IS NOT NULL AND agent_id != '') AS agent_count
                FROM mc_tasks
                WHERE project IS NOT NULL
                GROUP BY project
            ) tc ON tc.project = p.id
            ORDER BY p."order", p.name
        """)
        )
        rows = result.all()
        projects = []
        for row in rows:
            m = _row_to_project_dict(row)
            projects.append(ProjectWithCounts(**m))
        return projects


async def get_project(project_id: str) -> ProjectDetail | None:
    async with async_session() as session:
        # Fetch project
        result = await session.execute(
            text("SELECT * FROM mc_projects WHERE id = :id"),
            {"id": project_id},
        )
        row = result.first()
        if row is None:
            return None

        proj = _row_to_project_dict(row)

        # Fetch tasks
        tasks_result = await session.execute(
            text("""
                SELECT id, title, state, priority, agent_id, tags,
                       created_at, updated_at, completed_at
                FROM mc_tasks
                WHERE project = :project_id
                ORDER BY priority, created_at DESC
            """),
            {"project_id": project_id},
        )
        tasks = []
        agent_ids_set: set[str] = set()
        for t in tasks_result.all():
            tm = dict(t._mapping)
            tags = tm.get("tags") or []
            tasks.append(
                TaskSummary(
                    id=tm["id"],
                    title=tm["title"],
                    state=tm["state"],
                    priority=tm["priority"],
                    agent_id=tm["agent_id"],
                    tags=tags if isinstance(tags, list) else [],
                    created_at=tm.get("created_at"),
                    updated_at=tm.get("updated_at"),
                    completed_at=tm.get("completed_at"),
                )
            )
            if tm["agent_id"]:
                agent_ids_set.add(tm["agent_id"])

        return ProjectDetail(
            **proj,
            task_count=len(tasks),
            agent_count=len(agent_ids_set),
            tasks=tasks,
            agent_ids=sorted(agent_ids_set),
        )


async def create_project(payload: ProjectCreate) -> ProjectWithCounts:
    async with async_session() as session:
        docs_json = json.dumps([d.model_dump() for d in payload.docs]) if payload.docs else "[]"
        await session.execute(
            text("""
                INSERT INTO mc_projects (id, name, icon, color, description, docs, status, "order")
                VALUES (:id, :name, :icon, :color, :description, CAST(:docs AS jsonb), :status, :order)
            """),
            {
                "id": payload.id,
                "name": payload.name,
                "icon": payload.icon,
                "color": payload.color,
                "description": payload.description,
                "docs": docs_json,
                "status": payload.status,
                "order": payload.order,
            },
        )
        await session.commit()

        # Re-fetch to get timestamps
        result = await session.execute(
            text("SELECT * FROM mc_projects WHERE id = :id"),
            {"id": payload.id},
        )
        row = result.first()
        proj = _row_to_project_dict(row)
        return ProjectWithCounts(**proj, task_count=0, agent_count=0)


async def update_project(project_id: str, payload: ProjectUpdate) -> ProjectWithCounts | None:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        # Nothing to update, just return current
        proj = await get_project(project_id)
        if proj is None:
            return None
        return ProjectWithCounts(**proj.model_dump(exclude={"tasks", "agent_ids"}))

    async with async_session() as session:
        # Check exists
        check = await session.execute(
            text("SELECT id FROM mc_projects WHERE id = :id"),
            {"id": project_id},
        )
        if check.first() is None:
            return None

        # Build dynamic SET clause
        set_parts = []
        params: dict = {"id": project_id}
        for key, value in updates.items():
            if key == "docs":
                set_parts.append("docs = CAST(:docs AS jsonb)")
                params["docs"] = json.dumps(
                    [d.model_dump() if hasattr(d, "model_dump") else d for d in value]
                )
            elif key == "order":
                set_parts.append('"order" = :order_val')
                params["order_val"] = value
            else:
                set_parts.append(f"{key} = :{key}")
                params[key] = value

        query = f"UPDATE mc_projects SET {', '.join(set_parts)} WHERE id = :id"
        await session.execute(text(query), params)
        await session.commit()

        # Re-fetch with counts
        result = await session.execute(
            text("""
            SELECT p.*,
                   COALESCE(tc.task_count, 0) AS task_count,
                   COALESCE(tc.agent_count, 0) AS agent_count
            FROM mc_projects p
            LEFT JOIN (
                SELECT project,
                       COUNT(*) AS task_count,
                       COUNT(DISTINCT agent_id) FILTER (WHERE agent_id IS NOT NULL AND agent_id != '') AS agent_count
                FROM mc_tasks
                WHERE project IS NOT NULL
                GROUP BY project
            ) tc ON tc.project = p.id
            WHERE p.id = :id
        """),
            {"id": project_id},
        )
        row = result.first()
        m = _row_to_project_dict(row)
        return ProjectWithCounts(**m)


async def delete_project(project_id: str) -> tuple[bool, str | None]:
    async with async_session() as session:
        # Check for tasks
        task_check = await session.execute(
            text("SELECT COUNT(*) FROM mc_tasks WHERE project = :id"),
            {"id": project_id},
        )
        count = task_check.scalar()
        if count and count > 0:
            return (
                False,
                "Cannot delete project with existing tasks. Reassign or delete tasks first.",
            )

        result = await session.execute(
            text("DELETE FROM mc_projects WHERE id = :id"),
            {"id": project_id},
        )
        await session.commit()
        if result.rowcount == 0:
            return False, "Project not found"
        return True, None
