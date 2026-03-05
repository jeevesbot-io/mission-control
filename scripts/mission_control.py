#!/usr/bin/env python3
"""
Mission Control API Wrapper
============================

CLI and Python API for CRUD operations on Mission Control database tables:
mc_tasks, mc_comments, mc_notifications, mc_activity.

Usage (CLI):
    # List all tasks
    python mission_control.py tasks list

    # List tasks filtered by state/agent
    python mission_control.py tasks list --state in_progress --agent builder

    # Get a single task
    python mission_control.py tasks get 42

    # Create a task
    python mission_control.py tasks create --title "Fix bug" --agent-id builder --created-by jeeves

    # Update a task
    python mission_control.py tasks update 42 --priority 1 --state todo

    # Change task state
    python mission_control.py tasks set-state 42 review

    # List comments on a task
    python mission_control.py comments list 42

    # Add a comment
    python mission_control.py comments add 42 --author builder --body "Done, ready for review"

    # List notifications
    python mission_control.py notifications list builder
    python mission_control.py notifications list builder --all

    # Mark notification read
    python mission_control.py notifications read 7

    # Create notification
    python mission_control.py notifications create --agent builder --task-id 42 \\
        --type assigned --message "You've been assigned task #42"

    # Log activity
    python mission_control.py activity log --task-id 42 --agent builder \\
        --action created --detail "Task created from CLI"

Usage (Python):
    import asyncio
    from mission_control import MissionControlDB

    async def main():
        db = MissionControlDB()
        await db.connect()
        tasks = await db.list_tasks(state="in_progress")
        print(tasks)
        await db.close()

    asyncio.run(main())

Connection: postgresql://jeeves@localhost:5432/jeeves (no password)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, datetime
from typing import Any

import asyncpg

# -- Constants --

DSN = "postgresql://jeeves@localhost:5432/jeeves"

VALID_STATES = (
    "backlog", "todo", "in_progress", "blocked",
    "peer_review", "rejected", "review", "done", "cancelled",
)

VALID_COMMENT_TYPES = ("comment", "review", "approval", "rejection", "status_change")

VALID_NOTIFICATION_TYPES = (
    "mention", "assigned", "review_requested",
    "review_complete", "state_change", "comment",
)

VALID_ACTIONS = (
    "created", "state_changed", "assigned",
    "commented", "reviewed", "approved", "rejected",
)


# -- Database API --

class MissionControlDB:
    """Async wrapper for Mission Control database operations."""

    def __init__(self, dsn: str = DSN) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Establish connection pool."""
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()

    @property
    def pool(self) -> asyncpg.Pool:
        if not self._pool:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._pool

    # -- mc_tasks --

    async def list_tasks(
        self,
        state: str | None = None,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List tasks, optionally filtered by state and/or agent_id."""
        query = "SELECT * FROM mc_tasks WHERE 1=1"
        params: list[Any] = []
        idx = 0

        if state:
            idx += 1
            query += f" AND state = ${idx}"
            params.append(state)
        if agent_id:
            idx += 1
            query += f" AND agent_id = ${idx}"
            params.append(agent_id)

        query += " ORDER BY priority ASC, created_at DESC"
        rows = await self.pool.fetch(query, *params)
        return [dict(r) for r in rows]

    async def get_task(self, task_id: int) -> dict[str, Any] | None:
        """Get a single task by ID."""
        row = await self.pool.fetchrow("SELECT * FROM mc_tasks WHERE id = $1", task_id)
        return dict(row) if row else None

    async def create_task(
        self,
        title: str,
        agent_id: str,
        created_by: str,
        *,
        description: str | None = None,
        reviewer_id: str | None = None,
        state: str = "backlog",
        priority: int = 3,
        labels: list[str] | None = None,
        parent_task_id: int | None = None,
        due_date: date | None = None,
    ) -> dict[str, Any]:
        """Create a new task. Returns the created row."""
        row = await self.pool.fetchrow(
            """
            INSERT INTO mc_tasks
                (title, description, agent_id, reviewer_id, created_by,
                 state, priority, labels, parent_task_id, due_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
            """,
            title, description, agent_id, reviewer_id, created_by,
            state, priority, labels, parent_task_id, due_date,
        )
        return dict(row)

    async def update_task(self, task_id: int, **kwargs: Any) -> dict[str, Any] | None:
        """Update task fields. Pass only the columns to change."""
        allowed = {
            "title", "description", "agent_id", "reviewer_id",
            "state", "priority", "labels", "parent_task_id", "due_date",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return await self.get_task(task_id)

        set_clauses = []
        params: list[Any] = []
        for idx, (col, val) in enumerate(updates.items(), start=1):
            set_clauses.append(f"{col} = ${idx}")
            params.append(val)

        params.append(task_id)
        query = f"UPDATE mc_tasks SET {', '.join(set_clauses)} WHERE id = ${len(params)} RETURNING *"
        row = await self.pool.fetchrow(query, *params)
        return dict(row) if row else None

    async def update_task_state(self, task_id: int, state: str) -> dict[str, Any] | None:
        """Change a task's state. Validates against allowed states."""
        if state not in VALID_STATES:
            raise ValueError(f"Invalid state '{state}'. Must be one of: {VALID_STATES}")
        return await self.update_task(task_id, state=state)

    # -- mc_comments --

    async def list_comments(self, task_id: int) -> list[dict[str, Any]]:
        """List all comments for a task, oldest first."""
        rows = await self.pool.fetch(
            "SELECT * FROM mc_comments WHERE task_id = $1 ORDER BY created_at ASC",
            task_id,
        )
        return [dict(r) for r in rows]

    async def add_comment(
        self,
        task_id: int,
        author_id: str,
        body: str,
        *,
        comment_type: str = "comment",
    ) -> dict[str, Any]:
        """Add a comment to a task."""
        if comment_type not in VALID_COMMENT_TYPES:
            raise ValueError(f"Invalid comment_type '{comment_type}'. Must be one of: {VALID_COMMENT_TYPES}")
        row = await self.pool.fetchrow(
            """
            INSERT INTO mc_comments (task_id, author_id, body, comment_type)
            VALUES ($1, $2, $3, $4) RETURNING *
            """,
            task_id, author_id, body, comment_type,
        )
        return dict(row)

    # -- mc_notifications --

    async def list_notifications(
        self,
        agent_id: str,
        unread_only: bool = True,
    ) -> list[dict[str, Any]]:
        """List notifications for an agent. Defaults to unread only."""
        if unread_only:
            rows = await self.pool.fetch(
                "SELECT * FROM mc_notifications WHERE agent_id = $1 AND read = false ORDER BY created_at DESC",
                agent_id,
            )
        else:
            rows = await self.pool.fetch(
                "SELECT * FROM mc_notifications WHERE agent_id = $1 ORDER BY created_at DESC",
                agent_id,
            )
        return [dict(r) for r in rows]

    async def mark_read(self, notification_id: int) -> dict[str, Any] | None:
        """Mark a notification as read."""
        row = await self.pool.fetchrow(
            "UPDATE mc_notifications SET read = true WHERE id = $1 RETURNING *",
            notification_id,
        )
        return dict(row) if row else None

    async def create_notification(
        self,
        agent_id: str,
        task_id: int,
        notification_type: str,
        message: str,
    ) -> dict[str, Any]:
        """Create a notification for an agent."""
        if notification_type not in VALID_NOTIFICATION_TYPES:
            raise ValueError(
                f"Invalid type '{notification_type}'. Must be one of: {VALID_NOTIFICATION_TYPES}"
            )
        row = await self.pool.fetchrow(
            """
            INSERT INTO mc_notifications (agent_id, task_id, type, message)
            VALUES ($1, $2, $3, $4) RETURNING *
            """,
            agent_id, task_id, notification_type, message,
        )
        return dict(row)

    # -- mc_activity --

    async def log_activity(
        self,
        task_id: int,
        agent_id: str,
        action: str,
        detail: str | None = None,
    ) -> dict[str, Any]:
        """Log an activity event for a task."""
        if action not in VALID_ACTIONS:
            raise ValueError(f"Invalid action '{action}'. Must be one of: {VALID_ACTIONS}")
        row = await self.pool.fetchrow(
            """
            INSERT INTO mc_activity (task_id, agent_id, action, detail)
            VALUES ($1, $2, $3, $4) RETURNING *
            """,
            task_id, agent_id, action, detail,
        )
        return dict(row)


# -- JSON serializer for CLI output --

def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=_json_default))


# -- CLI --

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mission_control",
        description="CLI for Mission Control database operations",
    )
    parser.add_argument("--dsn", default=DSN, help="PostgreSQL DSN")
    sub = parser.add_subparsers(dest="resource", required=True)

    # -- tasks --
    tasks = sub.add_parser("tasks", help="Task operations")
    tasks_sub = tasks.add_subparsers(dest="action", required=True)

    t_list = tasks_sub.add_parser("list", help="List tasks")
    t_list.add_argument("--state", choices=VALID_STATES)
    t_list.add_argument("--agent", dest="agent_id")

    t_get = tasks_sub.add_parser("get", help="Get a task by ID")
    t_get.add_argument("id", type=int)

    t_create = tasks_sub.add_parser("create", help="Create a task")
    t_create.add_argument("--title", required=True)
    t_create.add_argument("--agent-id", required=True)
    t_create.add_argument("--created-by", required=True)
    t_create.add_argument("--description")
    t_create.add_argument("--reviewer-id")
    t_create.add_argument("--state", default="backlog", choices=VALID_STATES)
    t_create.add_argument("--priority", type=int, default=3, choices=[1, 2, 3, 4])
    t_create.add_argument("--labels", nargs="*")
    t_create.add_argument("--parent-task-id", type=int)
    t_create.add_argument("--due-date", help="YYYY-MM-DD")

    t_update = tasks_sub.add_parser("update", help="Update a task")
    t_update.add_argument("id", type=int)
    t_update.add_argument("--title")
    t_update.add_argument("--description")
    t_update.add_argument("--agent-id")
    t_update.add_argument("--reviewer-id")
    t_update.add_argument("--state", choices=VALID_STATES)
    t_update.add_argument("--priority", type=int, choices=[1, 2, 3, 4])
    t_update.add_argument("--labels", nargs="*")

    t_state = tasks_sub.add_parser("set-state", help="Change task state")
    t_state.add_argument("id", type=int)
    t_state.add_argument("state", choices=VALID_STATES)

    # -- comments --
    comments = sub.add_parser("comments", help="Comment operations")
    comments_sub = comments.add_subparsers(dest="action", required=True)

    c_list = comments_sub.add_parser("list", help="List comments for a task")
    c_list.add_argument("task_id", type=int)

    c_add = comments_sub.add_parser("add", help="Add a comment")
    c_add.add_argument("task_id", type=int)
    c_add.add_argument("--author", required=True)
    c_add.add_argument("--body", required=True)
    c_add.add_argument("--type", dest="comment_type", default="comment", choices=VALID_COMMENT_TYPES)

    # -- notifications --
    notifs = sub.add_parser("notifications", help="Notification operations")
    notifs_sub = notifs.add_subparsers(dest="action", required=True)

    n_list = notifs_sub.add_parser("list", help="List notifications for an agent")
    n_list.add_argument("agent_id")
    n_list.add_argument("--all", dest="show_all", action="store_true", help="Include read notifications")

    n_read = notifs_sub.add_parser("read", help="Mark a notification as read")
    n_read.add_argument("id", type=int)

    n_create = notifs_sub.add_parser("create", help="Create a notification")
    n_create.add_argument("--agent", dest="agent_id", required=True)
    n_create.add_argument("--task-id", type=int, required=True)
    n_create.add_argument("--type", dest="ntype", required=True, choices=VALID_NOTIFICATION_TYPES)
    n_create.add_argument("--message", required=True)

    # -- activity --
    activity = sub.add_parser("activity", help="Activity log operations")
    activity_sub = activity.add_subparsers(dest="action", required=True)

    a_log = activity_sub.add_parser("log", help="Log an activity event")
    a_log.add_argument("--task-id", type=int, required=True)
    a_log.add_argument("--agent", dest="agent_id", required=True)
    a_log.add_argument("--action", dest="act", required=True, choices=VALID_ACTIONS)
    a_log.add_argument("--detail")

    return parser


async def run_cli(args: argparse.Namespace) -> None:
    db = MissionControlDB(dsn=args.dsn)
    await db.connect()

    try:
        if args.resource == "tasks":
            if args.action == "list":
                result = await db.list_tasks(state=args.state, agent_id=args.agent_id)
                _print_json(result)
            elif args.action == "get":
                result = await db.get_task(args.id)
                if result is None:
                    print(f"Task {args.id} not found.", file=sys.stderr)
                    sys.exit(1)
                _print_json(result)
            elif args.action == "create":
                due = date.fromisoformat(args.due_date) if args.due_date else None
                result = await db.create_task(
                    title=args.title,
                    agent_id=args.agent_id,
                    created_by=args.created_by,
                    description=args.description,
                    reviewer_id=args.reviewer_id,
                    state=args.state,
                    priority=args.priority,
                    labels=args.labels,
                    parent_task_id=args.parent_task_id,
                    due_date=due,
                )
                _print_json(result)
            elif args.action == "update":
                kwargs: dict[str, Any] = {}
                for field in ("title", "description", "state", "priority", "labels"):
                    val = getattr(args, field, None)
                    if val is not None:
                        kwargs[field] = val
                if args.agent_id:
                    kwargs["agent_id"] = args.agent_id
                if args.reviewer_id:
                    kwargs["reviewer_id"] = args.reviewer_id
                result = await db.update_task(args.id, **kwargs)
                if result is None:
                    print(f"Task {args.id} not found.", file=sys.stderr)
                    sys.exit(1)
                _print_json(result)
            elif args.action == "set-state":
                result = await db.update_task_state(args.id, args.state)
                if result is None:
                    print(f"Task {args.id} not found.", file=sys.stderr)
                    sys.exit(1)
                _print_json(result)

        elif args.resource == "comments":
            if args.action == "list":
                result = await db.list_comments(args.task_id)
                _print_json(result)
            elif args.action == "add":
                result = await db.add_comment(
                    task_id=args.task_id,
                    author_id=args.author,
                    body=args.body,
                    comment_type=args.comment_type,
                )
                _print_json(result)

        elif args.resource == "notifications":
            if args.action == "list":
                result = await db.list_notifications(
                    agent_id=args.agent_id,
                    unread_only=not args.show_all,
                )
                _print_json(result)
            elif args.action == "read":
                result = await db.mark_read(args.id)
                if result is None:
                    print(f"Notification {args.id} not found.", file=sys.stderr)
                    sys.exit(1)
                _print_json(result)
            elif args.action == "create":
                result = await db.create_notification(
                    agent_id=args.agent_id,
                    task_id=args.task_id,
                    notification_type=args.ntype,
                    message=args.message,
                )
                _print_json(result)

        elif args.resource == "activity":
            if args.action == "log":
                result = await db.log_activity(
                    task_id=args.task_id,
                    agent_id=args.agent_id,
                    action=args.act,
                    detail=args.detail,
                )
                _print_json(result)

    finally:
        await db.close()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run_cli(args))


if __name__ == "__main__":
    main()
