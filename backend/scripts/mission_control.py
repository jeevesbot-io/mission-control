#!/usr/bin/env python3
"""mission_control.py — Python API for Mission Control mc_* tables.

Provides CRUD wrappers for mc_tasks, mc_comments, mc_notifications, mc_activity.
Used by agents and cron jobs to interact with the War Room without going through
the FastAPI HTTP layer.

Usage (CLI):
    python scripts/mission_control.py tasks list
    python scripts/mission_control.py tasks get 76
    python scripts/mission_control.py tasks queue
    python scripts/mission_control.py tasks claim 76 --agent jeeves
    python scripts/mission_control.py tasks complete 76 --result "Done" --proof '{"test_output":"..."}'
    python scripts/mission_control.py tasks release 76
    python scripts/mission_control.py comments list 76
    python scripts/mission_control.py comments add 76 --author jeeves --body "LGTM"
    python scripts/mission_control.py notifications list --agent jeeves
    python scripts/mission_control.py notifications unread --agent jeeves
    python scripts/mission_control.py notifications mark-read 15
    python scripts/mission_control.py activity list 76
    python scripts/mission_control.py activity log --task 76 --agent jeeves --action "peer_review.approved" --detail "Looks good"

Usage (Python API):
    from scripts.mission_control import MC
    import asyncio

    async def main():
        mc = MC()
        tasks = await mc.tasks.queue()
        task = await mc.tasks.claim(76, agent_id="jeeves")
        await mc.notifications.mark_read(15)
        await mc.activity.log(task_id=76, agent_id="jeeves", action="approved", detail="All good")

    asyncio.run(main())
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import asyncpg

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://jeeves@localhost:5432/jeeves",
)


async def _get_conn() -> asyncpg.Connection:
    return await asyncpg.connect(_DSN)


# ---------------------------------------------------------------------------
# Data models (simple dataclasses — no Pydantic dependency)
# ---------------------------------------------------------------------------


@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    state: str = "todo"
    priority: int = 3
    type: str = "feature"
    project: str | None = None
    tags: list[str] = field(default_factory=list)
    skill: str | None = None
    agent_id: str | None = None
    reviewer_id: str | None = None
    created_by: str | None = None
    claimed_by: str | None = None
    claimed_at: datetime | None = None
    picked_up: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    error: str | None = None
    proof: dict | None = None
    slug: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "state": self.state,
            "priority": self.priority,
            "type": self.type,
            "project": self.project,
            "tags": self.tags,
            "skill": self.skill,
            "agent_id": self.agent_id,
            "reviewer_id": self.reviewer_id,
            "claimed_by": self.claimed_by,
            "picked_up": self.picked_up,
            "result": self.result,
            "error": self.error,
            "slug": self.slug,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class Comment:
    id: int
    task_id: int
    author_id: str
    body: str
    comment_type: str = "comment"
    created_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "author_id": self.author_id,
            "body": self.body,
            "comment_type": self.comment_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class Notification:
    id: int
    agent_id: str
    task_id: int | None
    type: str
    message: str
    read: bool = False
    created_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "type": self.type,
            "message": self.message,
            "read": self.read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ActivityEntry:
    id: int
    task_id: int | None
    agent_id: str
    action: str
    detail: str | None = None
    module: str | None = None
    created_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "detail": self.detail,
            "module": self.module,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _row_to_task(row: asyncpg.Record) -> Task:
    d = dict(row)
    tags = d.get("tags") or []
    proof_raw = d.get("proof")
    proof = json.loads(proof_raw) if isinstance(proof_raw, str) else proof_raw
    return Task(
        id=d["id"],
        title=d.get("title", ""),
        description=d.get("description") or "",
        state=d.get("state", "todo"),
        priority=d.get("priority", 3),
        type=d.get("type", "feature"),
        project=d.get("project"),
        tags=list(tags) if tags else [],
        skill=d.get("skill"),
        agent_id=d.get("agent_id"),
        reviewer_id=d.get("reviewer_id"),
        created_by=d.get("created_by"),
        claimed_by=d.get("claimed_by"),
        claimed_at=d.get("claimed_at"),
        picked_up=bool(d.get("picked_up", False)),
        started_at=d.get("started_at"),
        completed_at=d.get("completed_at"),
        result=d.get("result"),
        error=d.get("error"),
        proof=proof,
        slug=d.get("slug"),
        created_at=d.get("created_at"),
        updated_at=d.get("updated_at"),
    )


# ---------------------------------------------------------------------------
# Tasks API
# ---------------------------------------------------------------------------


class TasksAPI:
    async def list(
        self,
        *,
        project: str | None = None,
        state: str | None = None,
        priority: int | None = None,
        limit: int = 100,
    ) -> list[Task]:
        conn = await _get_conn()
        try:
            where_parts = []
            params: list[Any] = []
            i = 1
            if project:
                where_parts.append(f"project = ${i}")
                params.append(project)
                i += 1
            if state:
                where_parts.append(f"state = ${i}")
                params.append(state)
                i += 1
            if priority is not None:
                where_parts.append(f"priority = ${i}")
                params.append(priority)
                i += 1
            where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
            params.append(limit)
            rows = await conn.fetch(
                f"SELECT * FROM mc_tasks {where} ORDER BY priority ASC, created_at ASC LIMIT ${i}",
                *params,
            )
            return [_row_to_task(r) for r in rows]
        finally:
            await conn.close()

    async def get(self, task_id: int) -> Task | None:
        conn = await _get_conn()
        try:
            row = await conn.fetchrow("SELECT * FROM mc_tasks WHERE id = $1", task_id)
            return _row_to_task(row) if row else None
        finally:
            await conn.close()

    async def queue(self) -> list[Task]:
        """Return pickup-eligible tasks: state=todo, not picked up, not blocked."""
        conn = await _get_conn()
        try:
            rows = await conn.fetch("""
                SELECT * FROM mc_tasks
                WHERE state = 'todo'
                  AND (picked_up IS NULL OR picked_up = false)
                  AND (blocked_by IS NULL OR blocked_by = '{}')
                ORDER BY priority ASC, created_at ASC
            """)
            return [_row_to_task(r) for r in rows]
        finally:
            await conn.close()

    async def claim(self, task_id: int, *, agent_id: str) -> Task:
        """Atomically claim a task. Raises ValueError if already claimed."""
        conn = await _get_conn()
        try:
            async with conn.transaction():
                existing = await conn.fetchrow(
                    "SELECT id, claimed_by FROM mc_tasks WHERE id = $1 FOR UPDATE",
                    task_id,
                )
                if existing is None:
                    raise ValueError(f"Task {task_id} not found")
                if existing["claimed_by"] is not None:
                    raise ValueError(
                        f"Task {task_id} is already claimed by {existing['claimed_by']}"
                    )
                row = await conn.fetchrow(
                    """
                    UPDATE mc_tasks
                    SET claimed_by = $2, claimed_at = now(),
                        state = 'in_progress', picked_up = true,
                        started_at = COALESCE(started_at, now()),
                        updated_at = now()
                    WHERE id = $1
                    RETURNING *
                    """,
                    task_id,
                    agent_id,
                )
            return _row_to_task(row)
        finally:
            await conn.close()

    async def release(self, task_id: int) -> Task | None:
        """Release a claimed task back to todo state."""
        conn = await _get_conn()
        try:
            row = await conn.fetchrow(
                """
                UPDATE mc_tasks
                SET claimed_by = NULL, claimed_at = NULL,
                    state = 'todo', picked_up = false,
                    updated_at = now()
                WHERE id = $1
                RETURNING *
                """,
                task_id,
            )
            return _row_to_task(row) if row else None
        finally:
            await conn.close()

    async def complete(
        self,
        task_id: int,
        *,
        result: str | None = None,
        error: str | None = None,
        proof: dict | None = None,
    ) -> Task | None:
        """Mark task as done. Requires at least one proof field."""
        if not proof or not any(proof.values()):
            raise ValueError(
                "Proof of work required. Provide at least one of: "
                "pr_url, ci_status, test_output, files_changed"
            )
        conn = await _get_conn()
        try:
            row = await conn.fetchrow(
                """
                UPDATE mc_tasks
                SET state = 'done', result = $2, error = $3,
                    proof = $4::jsonb, completed_at = now(), updated_at = now()
                WHERE id = $1
                RETURNING *
                """,
                task_id,
                result,
                error,
                json.dumps(proof),
            )
            return _row_to_task(row) if row else None
        finally:
            await conn.close()

    async def update_state(self, task_id: int, *, state: str) -> Task | None:
        """Update a task's state directly (e.g. todo → peer_review → done)."""
        conn = await _get_conn()
        try:
            row = await conn.fetchrow(
                "UPDATE mc_tasks SET state = $2, updated_at = now() WHERE id = $1 RETURNING *",
                task_id,
                state,
            )
            return _row_to_task(row) if row else None
        finally:
            await conn.close()

    async def pending_reviews(self, *, reviewer_id: str) -> list[Task]:
        """Tasks awaiting peer review by a specific agent."""
        conn = await _get_conn()
        try:
            rows = await conn.fetch(
                "SELECT * FROM mc_tasks WHERE reviewer_id = $1 AND state = 'peer_review' ORDER BY created_at ASC",
                reviewer_id,
            )
            return [_row_to_task(r) for r in rows]
        finally:
            await conn.close()


# ---------------------------------------------------------------------------
# Comments API
# ---------------------------------------------------------------------------


class CommentsAPI:
    async def list(self, task_id: int, *, limit: int = 50) -> list[Comment]:
        conn = await _get_conn()
        try:
            rows = await conn.fetch(
                """
                SELECT id, task_id, author_id, body, comment_type, created_at
                FROM mc_comments WHERE task_id = $1
                ORDER BY created_at DESC LIMIT $2
                """,
                task_id,
                limit,
            )
            return [
                Comment(
                    id=r["id"],
                    task_id=r["task_id"],
                    author_id=r["author_id"],
                    body=r["body"],
                    comment_type=r["comment_type"] or "comment",
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            await conn.close()

    async def add(
        self,
        task_id: int,
        *,
        author_id: str,
        body: str,
        comment_type: str = "comment",
    ) -> Comment:
        conn = await _get_conn()
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO mc_comments (task_id, author_id, body, comment_type)
                VALUES ($1, $2, $3, $4)
                RETURNING id, task_id, author_id, body, comment_type, created_at
                """,
                task_id,
                author_id,
                body,
                comment_type,
            )
            return Comment(
                id=row["id"],
                task_id=row["task_id"],
                author_id=row["author_id"],
                body=row["body"],
                comment_type=row["comment_type"] or "comment",
                created_at=row["created_at"],
            )
        finally:
            await conn.close()

    async def delete(self, comment_id: int) -> bool:
        conn = await _get_conn()
        try:
            result = await conn.execute("DELETE FROM mc_comments WHERE id = $1", comment_id)
            return result != "DELETE 0"
        finally:
            await conn.close()


# ---------------------------------------------------------------------------
# Notifications API
# ---------------------------------------------------------------------------


class NotificationsAPI:
    async def list(
        self,
        *,
        agent_id: str | None = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        conn = await _get_conn()
        try:
            where_parts = []
            params: list[Any] = []
            i = 1
            if agent_id:
                where_parts.append(f"agent_id = ${i}")
                params.append(agent_id)
                i += 1
            if unread_only:
                where_parts.append("read = false")
            where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
            params.append(limit)
            rows = await conn.fetch(
                f"SELECT * FROM mc_notifications {where} ORDER BY created_at DESC LIMIT ${i}",
                *params,
            )
            return [
                Notification(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    task_id=r["task_id"],
                    type=r["type"],
                    message=r["message"],
                    read=bool(r["read"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            await conn.close()

    async def unread(self, *, agent_id: str) -> list[Notification]:
        """Shortcut: unread review/mention notifications for an agent."""
        conn = await _get_conn()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM mc_notifications
                WHERE agent_id = $1
                  AND read = false
                  AND type IN ('review_requested', 'mention')
                ORDER BY created_at ASC
                """,
                agent_id,
            )
            return [
                Notification(
                    id=r["id"],
                    agent_id=r["agent_id"],
                    task_id=r["task_id"],
                    type=r["type"],
                    message=r["message"],
                    read=bool(r["read"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            await conn.close()

    async def send(
        self,
        *,
        agent_id: str,
        message: str,
        type: str = "mention",
        task_id: int | None = None,
    ) -> Notification:
        """Create a notification for an agent."""
        conn = await _get_conn()
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO mc_notifications (agent_id, task_id, type, message, read, created_at)
                VALUES ($1, $2, $3, $4, false, now())
                RETURNING *
                """,
                agent_id,
                task_id,
                type,
                message,
            )
            return Notification(
                id=row["id"],
                agent_id=row["agent_id"],
                task_id=row["task_id"],
                type=row["type"],
                message=row["message"],
                read=bool(row["read"]),
                created_at=row["created_at"],
            )
        finally:
            await conn.close()

    async def mark_read(self, notification_id: int) -> bool:
        """Mark a notification as read."""
        conn = await _get_conn()
        try:
            result = await conn.execute(
                "UPDATE mc_notifications SET read = true WHERE id = $1", notification_id
            )
            return result != "UPDATE 0"
        finally:
            await conn.close()

    async def mark_all_read(self, *, agent_id: str) -> int:
        """Mark all notifications for an agent as read. Returns count."""
        conn = await _get_conn()
        try:
            result = await conn.execute(
                "UPDATE mc_notifications SET read = true WHERE agent_id = $1 AND read = false",
                agent_id,
            )
            return int(result.split()[-1])
        finally:
            await conn.close()


# ---------------------------------------------------------------------------
# Activity API
# ---------------------------------------------------------------------------


class ActivityAPI:
    async def list(self, task_id: int, *, limit: int = 50) -> list[ActivityEntry]:
        conn = await _get_conn()
        try:
            rows = await conn.fetch(
                """
                SELECT id, task_id, agent_id, action, detail, module, created_at
                FROM mc_activity WHERE task_id = $1
                ORDER BY created_at DESC LIMIT $2
                """,
                task_id,
                limit,
            )
            return [
                ActivityEntry(
                    id=r["id"],
                    task_id=r["task_id"],
                    agent_id=r["agent_id"],
                    action=r["action"],
                    detail=r["detail"],
                    module=r["module"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            await conn.close()

    async def log(
        self,
        *,
        agent_id: str,
        action: str,
        task_id: int | None = None,
        detail: str | None = None,
        module: str | None = None,
    ) -> ActivityEntry:
        """Log an activity entry."""
        conn = await _get_conn()
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO mc_activity (task_id, agent_id, action, detail, module, created_at)
                VALUES ($1, $2, $3, $4, $5, now())
                RETURNING id, task_id, agent_id, action, detail, module, created_at
                """,
                task_id,
                agent_id,
                action,
                detail,
                module,
            )
            return ActivityEntry(
                id=row["id"],
                task_id=row["task_id"],
                agent_id=row["agent_id"],
                action=row["action"],
                detail=row["detail"],
                module=row["module"],
                created_at=row["created_at"],
            )
        finally:
            await conn.close()

    async def recent(self, *, limit: int = 50, module: str | None = None) -> list[ActivityEntry]:
        """Recent activity across all tasks."""
        conn = await _get_conn()
        try:
            if module:
                rows = await conn.fetch(
                    "SELECT id, task_id, agent_id, action, detail, module, created_at FROM mc_activity WHERE module = $1 ORDER BY created_at DESC LIMIT $2",
                    module,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT id, task_id, agent_id, action, detail, module, created_at FROM mc_activity ORDER BY created_at DESC LIMIT $1",
                    limit,
                )
            return [
                ActivityEntry(
                    id=r["id"],
                    task_id=r["task_id"],
                    agent_id=r["agent_id"],
                    action=r["action"],
                    detail=r["detail"],
                    module=r["module"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            await conn.close()


# ---------------------------------------------------------------------------
# Top-level MC facade
# ---------------------------------------------------------------------------


class MC:
    """Main entry point for Mission Control operations.

    Usage:
        mc = MC()
        tasks = await mc.tasks.queue()
        notifs = await mc.notifications.unread(agent_id="jeeves")
    """

    def __init__(self):
        self.tasks = TasksAPI()
        self.comments = CommentsAPI()
        self.notifications = NotificationsAPI()
        self.activity = ActivityAPI()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_json(obj: Any):
    if hasattr(obj, "to_dict"):
        print(json.dumps(obj.to_dict(), indent=2, default=str))
    elif isinstance(obj, list):
        print(
            json.dumps(
                [o.to_dict() if hasattr(o, "to_dict") else o for o in obj], indent=2, default=str
            )
        )
    else:
        print(json.dumps(obj, indent=2, default=str))


async def _cli(args: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Mission Control CLI — mc_tasks, mc_comments, mc_notifications, mc_activity"
    )
    sub = parser.add_subparsers(dest="resource", required=True)

    # tasks
    t = sub.add_parser("tasks", help="Task operations")
    t_sub = t.add_subparsers(dest="action", required=True)
    t_sub.add_parser("list").add_argument("--project", default=None)
    t_sub.add_parser("queue")
    t_get = t_sub.add_parser("get")
    t_get.add_argument("id", type=int)
    t_claim = t_sub.add_parser("claim")
    t_claim.add_argument("id", type=int)
    t_claim.add_argument("--agent", required=True)
    t_release = t_sub.add_parser("release")
    t_release.add_argument("id", type=int)
    t_complete = t_sub.add_parser("complete")
    t_complete.add_argument("id", type=int)
    t_complete.add_argument("--result", default=None)
    t_complete.add_argument("--error", default=None)
    t_complete.add_argument("--proof", default=None, help="JSON string")
    t_reviews = t_sub.add_parser("pending-reviews")
    t_reviews.add_argument("--reviewer", required=True)

    # comments
    c = sub.add_parser("comments", help="Comment operations")
    c_sub = c.add_subparsers(dest="action", required=True)
    c_list = c_sub.add_parser("list")
    c_list.add_argument("task_id", type=int)
    c_add = c_sub.add_parser("add")
    c_add.add_argument("task_id", type=int)
    c_add.add_argument("--author", required=True)
    c_add.add_argument("--body", required=True)
    c_add.add_argument("--type", default="comment", dest="comment_type")

    # notifications
    n = sub.add_parser("notifications", help="Notification operations")
    n_sub = n.add_subparsers(dest="action", required=True)
    n_list = n_sub.add_parser("list")
    n_list.add_argument("--agent", default=None)
    n_unread = n_sub.add_parser("unread")
    n_unread.add_argument("--agent", required=True)
    n_send = n_sub.add_parser("send")
    n_send.add_argument("--agent", required=True)
    n_send.add_argument("--message", required=True)
    n_send.add_argument("--type", default="mention", dest="notif_type")
    n_send.add_argument("--task", type=int, default=None)
    n_read = n_sub.add_parser("mark-read")
    n_read.add_argument("id", type=int)
    n_read_all = n_sub.add_parser("mark-all-read")
    n_read_all.add_argument("--agent", required=True)

    # activity
    a = sub.add_parser("activity", help="Activity log operations")
    a_sub = a.add_subparsers(dest="action", required=True)
    a_list = a_sub.add_parser("list")
    a_list.add_argument("task_id", type=int)
    a_recent = a_sub.add_parser("recent")
    a_recent.add_argument("--module", default=None)
    a_recent.add_argument("--limit", type=int, default=20)
    a_log = a_sub.add_parser("log")
    a_log.add_argument("--task", type=int, default=None)
    a_log.add_argument("--agent", required=True)
    a_log.add_argument("--action", required=True, dest="log_action")
    a_log.add_argument("--detail", default=None)
    a_log.add_argument("--module", default=None)

    parsed = parser.parse_args(args)
    mc = MC()

    if parsed.resource == "tasks":
        if parsed.action == "list":
            _print_json(await mc.tasks.list(project=getattr(parsed, "project", None)))
        elif parsed.action == "queue":
            _print_json(await mc.tasks.queue())
        elif parsed.action == "get":
            task = await mc.tasks.get(parsed.id)
            _print_json(task) if task else print("Not found", file=sys.stderr)
        elif parsed.action == "claim":
            try:
                _print_json(await mc.tasks.claim(parsed.id, agent_id=parsed.agent))
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        elif parsed.action == "release":
            result = await mc.tasks.release(parsed.id)
            _print_json(result) if result else print("Not found", file=sys.stderr)
        elif parsed.action == "complete":
            proof = json.loads(parsed.proof) if parsed.proof else None
            try:
                result = await mc.tasks.complete(
                    parsed.id, result=parsed.result, error=parsed.error, proof=proof
                )
                _print_json(result)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        elif parsed.action == "pending-reviews":
            _print_json(await mc.tasks.pending_reviews(reviewer_id=parsed.reviewer))

    elif parsed.resource == "comments":
        if parsed.action == "list":
            _print_json(await mc.comments.list(parsed.task_id))
        elif parsed.action == "add":
            _print_json(
                await mc.comments.add(
                    parsed.task_id,
                    author_id=parsed.author,
                    body=parsed.body,
                    comment_type=parsed.comment_type,
                )
            )

    elif parsed.resource == "notifications":
        if parsed.action == "list":
            _print_json(await mc.notifications.list(agent_id=getattr(parsed, "agent", None)))
        elif parsed.action == "unread":
            _print_json(await mc.notifications.unread(agent_id=parsed.agent))
        elif parsed.action == "send":
            _print_json(
                await mc.notifications.send(
                    agent_id=parsed.agent,
                    message=parsed.message,
                    type=parsed.notif_type,
                    task_id=parsed.task,
                )
            )
        elif parsed.action == "mark-read":
            ok = await mc.notifications.mark_read(parsed.id)
            print("ok" if ok else "not found")
        elif parsed.action == "mark-all-read":
            count = await mc.notifications.mark_all_read(agent_id=parsed.agent)
            print(f"Marked {count} notification(s) as read")

    elif parsed.resource == "activity":
        if parsed.action == "list":
            _print_json(await mc.activity.list(parsed.task_id))
        elif parsed.action == "recent":
            _print_json(await mc.activity.recent(limit=parsed.limit, module=parsed.module))
        elif parsed.action == "log":
            _print_json(
                await mc.activity.log(
                    task_id=parsed.task,
                    agent_id=parsed.agent,
                    action=parsed.log_action,
                    detail=parsed.detail,
                    module=parsed.module,
                )
            )


def main():
    asyncio.run(_cli())


if __name__ == "__main__":
    main()
