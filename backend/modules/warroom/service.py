"""War Room service — tasks, projects, skills, soul editor, usage, heartbeat, calendar."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.config import settings

from .models import (
    PRIORITY_ORDER,
    CalendarDay,
    HeartbeatResponse,
    HistoryEntry,
    ModelResponse,
    Project,
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
    UsageTier,
    WarRoomStats,
    WorkspaceFileResponse,
)

logger = logging.getLogger(__name__)

# Locks for concurrent file access
_tasks_lock = threading.Lock()
_projects_lock = threading.Lock()
_openclaw_lock = threading.Lock()

# Usage cache
@dataclass
class _UsageCache:
    computed_at: float
    result: UsageResponse

_usage_cache: _UsageCache | None = None
_USAGE_CACHE_TTL = 60  # seconds

# Allowed workspace file names
_ALLOWED_WORKSPACE_FILES = {"SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md"}

# Soul templates (ported directly from VidClaw server.js)
_SOUL_TEMPLATES: list[SoulTemplate] = [
    SoulTemplate(
        name="Minimal Assistant",
        description="Bare bones, helpful, no personality",
        content="# SOUL.md\nBe helpful. Be concise. No fluff.",
    ),
    SoulTemplate(
        name="Friendly Companion",
        description="Warm, conversational, uses emoji",
        content=(
            "# SOUL.md - Who You Are\n"
            "You're warm, friendly, and genuinely care about helping. Use emoji naturally (not excessively). "
            "Be conversational — talk like a smart friend, not a manual. Have opinions, crack jokes when "
            "appropriate, and remember: helpfulness > formality."
        ),
    ),
    SoulTemplate(
        name="Technical Expert",
        description="Precise, detailed, code-focused",
        content=(
            "# SOUL.md - Who You Are\n"
            "You are a senior technical consultant. Be precise, thorough, and opinionated about best practices. "
            "Prefer code examples over explanations. Flag anti-patterns when you see them. Don't sugarcoat — "
            "if something is wrong, say so directly. Efficiency matters."
        ),
    ),
    SoulTemplate(
        name="Creative Partner",
        description="Imaginative, brainstormy, enthusiastic",
        content=(
            "# SOUL.md - Who You Are\n"
            "You're a creative collaborator — curious, imaginative, and always looking for unexpected angles. "
            "Brainstorm freely. Suggest wild ideas alongside safe ones. Get excited about good concepts. "
            "Push creative boundaries while staying grounded in what's achievable."
        ),
    ),
    SoulTemplate(
        name="Stern Operator",
        description="No-nonsense, military-efficient, dry humor",
        content=(
            "# SOUL.md - Who You Are\n"
            "Mission first. Be direct, efficient, and zero-waste in communication. No pleasantries unless earned. "
            "Dry humor is acceptable. Report status clearly. Flag risks immediately. You don't ask permission "
            "for routine ops — you execute and report. Save the small talk for after the job's done."
        ),
    ),
    SoulTemplate(
        name="Sarcastic Sidekick",
        description="Witty, slightly snarky, still helpful",
        content=(
            "# SOUL.md - Who You Are\n"
            "You're helpful, but you're not going to pretend everything is sunshine and rainbows. Deliver "
            "assistance with a side of wit. Be sarcastic when it's funny, never when it's cruel. You still "
            "get the job done — you just have commentary while doing it. Think dry British humor meets "
            "competent engineer."
        ),
    ),
]

SESSION_LIMIT = 45_000_000   # ~45M tokens per 5h session window
WEEKLY_LIMIT = 180_000_000   # ~180M tokens per week


def _gen_id() -> str:
    """Generate a short random ID (same pattern as VidClaw)."""
    import random
    import string
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=8))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_duration(ms: float) -> str:
    """Format milliseconds as human-readable duration (e.g. '2h 15m')."""
    total_s = max(0, ms / 1000)
    total_m = int(total_s / 60)
    h = total_m // 60
    m = total_m % 60
    d = h // 24
    if d > 0:
        return f"{d}d {h % 24}h"
    return f"{h}h {m}m"


def _detect_ref_type(url: str) -> str:
    if url.startswith("obsidian://"):
        return "obsidian"
    if url.endswith(".md") or url.endswith(".txt"):
        return "doc"
    return "link"


class WarRoomService:
    """All War Room business logic — tasks, projects, skills, soul, usage, heartbeat, calendar."""

    # -------------------------------------------------------------------------
    # Paths
    # -------------------------------------------------------------------------

    @property
    def _tasks_file(self) -> Path:
        return settings.dashboard_data_path / "tasks.json"

    @property
    def _projects_file(self) -> Path:
        return settings.dashboard_data_path / "projects.json"

    @property
    def _heartbeat_file(self) -> Path:
        return settings.dashboard_data_path / "heartbeat.json"

    @property
    def _openclaw_json(self) -> Path:
        return settings.openclaw_path / "openclaw.json"

    def _history_file(self, name: str) -> Path:
        return settings.dashboard_data_path / f"{name}-history.json"

    # -------------------------------------------------------------------------
    # Low-level JSON helpers (sync, called via asyncio.to_thread)
    # -------------------------------------------------------------------------

    def _read_json_sync(self, path: Path, default):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _write_json_sync(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------

    def _read_tasks_sync(self) -> list[dict]:
        with _tasks_lock:
            return self._read_json_sync(self._tasks_file, [])

    @staticmethod
    def _sanitize_task(t: dict) -> dict:
        """Filter to Task model fields and normalize legacy reference formats."""
        data = {k: v for k, v in t.items() if k in Task.model_fields}
        refs = data.get("references")
        if refs and isinstance(refs, list):
            clean = []
            for r in refs:
                if not isinstance(r, dict):
                    continue
                # Skip refs missing required fields for the current schema
                if "id" not in r or "title" not in r or "url" not in r:
                    # Try to migrate legacy format (path -> url, missing id/createdAt)
                    migrated = {
                        "id": r.get("id", r.get("path", "")),
                        "title": r.get("title", r.get("path", "").split("/")[-1] if r.get("path") else ""),
                        "url": r.get("url", r.get("path", "")),
                        "type": r.get("type", "link"),
                        "createdAt": r.get("createdAt", ""),
                    }
                    # Normalize legacy type values
                    if migrated["type"] not in ("link", "obsidian", "doc"):
                        migrated["type"] = "link"
                    clean.append(migrated)
                else:
                    # Ensure type is valid
                    if r.get("type") not in ("link", "obsidian", "doc"):
                        r = {**r, "type": "link"}
                    clean.append(r)
            data["references"] = clean
        return data

    def _write_tasks_sync(self, tasks: list[dict]) -> None:
        with _tasks_lock:
            self._write_json_sync(self._tasks_file, tasks)

    async def list_tasks(
        self,
        project: str | None = None,
        priority: str | None = None,
        tags: str | None = None,
        status: str | None = None,
    ) -> list[Task]:
        raw = await asyncio.to_thread(self._read_tasks_sync)
        result = []
        tag_filter = [t.strip() for t in tags.split(",")] if tags else []
        for t in raw:
            if status and t.get("status") != status:
                continue
            if priority and t.get("priority") != priority:
                continue
            if project == "untagged":
                if t.get("project"):
                    continue
            elif project and t.get("project") != project:
                continue
            if tag_filter:
                task_tags = t.get("tags", [])
                if not any(tag in task_tags for tag in tag_filter):
                    continue
            result.append(Task(**self._sanitize_task(t)))
        return result

    async def get_task(self, task_id: str) -> Task | None:
        raw = await asyncio.to_thread(self._read_tasks_sync)
        for t in raw:
            if t.get("id") == task_id:
                return Task(**self._sanitize_task(t))
        return None

    async def create_task(self, payload: TaskCreate) -> Task:
        def _create():
            tasks = self._read_tasks_sync()
            now = _now_iso()
            task = {
                "id": _gen_id(),
                "title": payload.title or "Untitled",
                "description": payload.description or "",
                "priority": payload.priority,
                "skill": payload.skill or None,
                "status": payload.status,
                "project": payload.project,
                "tags": payload.tags or [],
                "schedule": payload.schedule,
                "scheduledAt": payload.scheduledAt,
                "references": [],
                "createdAt": now,
                "updatedAt": now,
                "completedAt": None,
                "startedAt": None,
                "result": None,
                "error": None,
                "pickedUp": False,
                "estimatedHours": payload.estimatedHours,
                "actualHours": None,
            }
            tasks.append(task)
            self._write_tasks_sync(tasks)
            return task

        raw = await asyncio.to_thread(_create)
        return Task(**self._sanitize_task(raw))

    async def update_task(self, task_id: str, payload: TaskUpdate) -> Task | None:
        def _update():
            tasks = self._read_tasks_sync()
            idx = next((i for i, t in enumerate(tasks) if t.get("id") == task_id), -1)
            if idx == -1:
                return None
            was_not_done = tasks[idx].get("status") != "done"
            updates = payload.model_dump(exclude_none=True)
            tasks[idx].update(updates)
            tasks[idx]["updatedAt"] = _now_iso()
            # Auto-set completedAt when transitioning to done
            if was_not_done and tasks[idx].get("status") == "done":
                if not tasks[idx].get("completedAt"):
                    tasks[idx]["completedAt"] = _now_iso()
            # Clear completedAt if moving out of done
            if tasks[idx].get("status") != "done":
                tasks[idx]["completedAt"] = None
            self._write_tasks_sync(tasks)
            return tasks[idx]

        raw = await asyncio.to_thread(_update)
        if raw is None:
            return None
        return Task(**self._sanitize_task(raw))

    async def delete_task(self, task_id: str) -> bool:
        def _delete():
            tasks = self._read_tasks_sync()
            new_tasks = [t for t in tasks if t.get("id") != task_id]
            if len(new_tasks) == len(tasks):
                return False
            self._write_tasks_sync(new_tasks)
            return True

        return await asyncio.to_thread(_delete)

    async def run_task(self, task_id: str) -> Task | None:
        def _run():
            tasks = self._read_tasks_sync()
            idx = next((i for i, t in enumerate(tasks) if t.get("id") == task_id), -1)
            if idx == -1:
                return None
            now = _now_iso()
            tasks[idx]["status"] = "in-progress"
            tasks[idx]["startedAt"] = now
            tasks[idx]["updatedAt"] = now
            self._write_tasks_sync(tasks)
            return tasks[idx]

        raw = await asyncio.to_thread(_run)
        if raw is None:
            return None
        return Task(**self._sanitize_task(raw))

    async def get_queue(self) -> list[Task]:
        """Return tasks eligible for agent pickup, sorted by priority."""
        raw = await asyncio.to_thread(self._read_tasks_sync)
        now = datetime.now(timezone.utc)
        queue: list[dict] = []

        for t in raw:
            status = t.get("status", "")
            # In-progress tasks triggered by Run Now but not yet picked up
            if status == "in-progress" and not t.get("pickedUp"):
                queue.append(t)
                continue
            if status != "todo":
                continue
            schedule = t.get("schedule")
            if not schedule or schedule in ("asap", "next-heartbeat"):
                queue.append(t)
                continue
            # Scheduled for specific time — only if time has passed
            try:
                sched_time = datetime.fromisoformat(schedule)
                if sched_time.tzinfo is None:
                    sched_time = sched_time.replace(tzinfo=timezone.utc)
                if sched_time <= now:
                    queue.append(t)
            except ValueError:
                queue.append(t)  # malformed schedule — include anyway

        queue.sort(key=lambda t: (
            PRIORITY_ORDER.get(t.get("priority", "medium"), 2),
            t.get("scheduledAt") or "",
        ))
        return [Task(**self._sanitize_task(t)) for t in queue]

    async def pickup_task(self, task_id: str) -> Task | None:
        def _pickup():
            tasks = self._read_tasks_sync()
            idx = next((i for i, t in enumerate(tasks) if t.get("id") == task_id), -1)
            if idx == -1:
                return None
            now = _now_iso()
            tasks[idx]["pickedUp"] = True
            tasks[idx]["status"] = "in-progress"
            tasks[idx]["startedAt"] = tasks[idx].get("startedAt") or now
            tasks[idx]["updatedAt"] = now
            self._write_tasks_sync(tasks)
            return tasks[idx]

        raw = await asyncio.to_thread(_pickup)
        if raw is None:
            return None
        return Task(**self._sanitize_task(raw))

    async def complete_task(self, task_id: str, payload: TaskComplete) -> Task | None:
        def _complete():
            tasks = self._read_tasks_sync()
            idx = next((i for i, t in enumerate(tasks) if t.get("id") == task_id), -1)
            if idx == -1:
                return None
            now = _now_iso()
            tasks[idx]["status"] = "done"
            tasks[idx]["completedAt"] = now
            tasks[idx]["updatedAt"] = now
            tasks[idx]["result"] = payload.result
            if payload.error:
                tasks[idx]["error"] = payload.error
            self._write_tasks_sync(tasks)
            return tasks[idx]

        raw = await asyncio.to_thread(_complete)
        if raw is None:
            return None
        return Task(**self._sanitize_task(raw))

    # -------------------------------------------------------------------------
    # References
    # -------------------------------------------------------------------------

    async def list_references(self, task_id: str) -> list[Reference] | None:
        raw = await asyncio.to_thread(self._read_tasks_sync)
        task = next((t for t in raw if t.get("id") == task_id), None)
        if task is None:
            return None
        return [Reference(**r) for r in task.get("references", [])]

    async def add_reference(self, task_id: str, payload: ReferenceCreate) -> Reference | None:
        def _add():
            tasks = self._read_tasks_sync()
            idx = next((i for i, t in enumerate(tasks) if t.get("id") == task_id), -1)
            if idx == -1:
                return None
            ref_type = payload.type or _detect_ref_type(payload.url)
            ref = {
                "id": _gen_id(),
                "title": payload.title,
                "url": payload.url,
                "type": ref_type,
                "createdAt": _now_iso(),
            }
            if "references" not in tasks[idx]:
                tasks[idx]["references"] = []
            tasks[idx]["references"].append(ref)
            tasks[idx]["updatedAt"] = _now_iso()
            self._write_tasks_sync(tasks)
            return ref

        raw = await asyncio.to_thread(_add)
        if raw is None:
            return None
        return Reference(**raw)

    async def delete_reference(self, task_id: str, ref_id: str) -> bool:
        def _del():
            tasks = self._read_tasks_sync()
            idx = next((i for i, t in enumerate(tasks) if t.get("id") == task_id), -1)
            if idx == -1:
                return False
            refs = tasks[idx].get("references", [])
            new_refs = [r for r in refs if r.get("id") != ref_id]
            if len(new_refs) == len(refs):
                return False
            tasks[idx]["references"] = new_refs
            tasks[idx]["updatedAt"] = _now_iso()
            self._write_tasks_sync(tasks)
            return True

        return await asyncio.to_thread(_del)

    # -------------------------------------------------------------------------
    # Projects
    # -------------------------------------------------------------------------

    def _read_projects_sync(self) -> list[dict]:
        with _projects_lock:
            return self._read_json_sync(self._projects_file, [])

    def _write_projects_sync(self, projects: list[dict]) -> None:
        with _projects_lock:
            self._write_json_sync(self._projects_file, projects)

    async def list_projects(self) -> list[ProjectWithCount]:
        raw_projects = await asyncio.to_thread(self._read_projects_sync)
        raw_tasks = await asyncio.to_thread(self._read_tasks_sync)
        task_counts: dict[str, int] = {}
        for t in raw_tasks:
            p = t.get("project")
            if p:
                task_counts[p] = task_counts.get(p, 0) + 1
        result = []
        for p in raw_projects:
            proj = Project(**{k: v for k, v in p.items() if k in Project.model_fields})
            result.append(ProjectWithCount(**proj.model_dump(), task_count=task_counts.get(proj.id, 0)))
        result.sort(key=lambda p: p.order)
        return result

    async def create_project(self, payload: ProjectCreate) -> Project:
        def _create():
            projects = self._read_projects_sync()
            project = payload.model_dump()
            projects.append(project)
            self._write_projects_sync(projects)
            return project

        raw = await asyncio.to_thread(_create)
        return Project(**raw)

    async def update_project(self, project_id: str, payload: ProjectUpdate) -> Project | None:
        def _update():
            projects = self._read_projects_sync()
            idx = next((i for i, p in enumerate(projects) if p.get("id") == project_id), -1)
            if idx == -1:
                return None
            updates = payload.model_dump(exclude_none=True)
            projects[idx].update(updates)
            self._write_projects_sync(projects)
            return projects[idx]

        raw = await asyncio.to_thread(_update)
        if raw is None:
            return None
        return Project(**{k: v for k, v in raw.items() if k in Project.model_fields})

    async def delete_project(self, project_id: str) -> tuple[bool, str | None]:
        """Returns (success, error_message). Error if tasks still reference this project."""
        raw_tasks = await asyncio.to_thread(self._read_tasks_sync)
        if any(t.get("project") == project_id for t in raw_tasks):
            return False, "Cannot delete project with existing tasks. Reassign or delete tasks first."

        def _delete():
            projects = self._read_projects_sync()
            new = [p for p in projects if p.get("id") != project_id]
            if len(new) == len(projects):
                return False
            self._write_projects_sync(new)
            return True

        ok = await asyncio.to_thread(_delete)
        return ok, None

    # -------------------------------------------------------------------------
    # Tags
    # -------------------------------------------------------------------------

    async def list_tags(self) -> list[str]:
        raw = await asyncio.to_thread(self._read_tasks_sync)
        tags: set[str] = set()
        for t in raw:
            for tag in t.get("tags", []):
                tags.add(tag)
        return sorted(tags)

    # -------------------------------------------------------------------------
    # Heartbeat
    # -------------------------------------------------------------------------

    async def get_heartbeat(self) -> HeartbeatResponse:
        def _read():
            return self._read_json_sync(self._heartbeat_file, {"lastHeartbeat": None})

        data = await asyncio.to_thread(_read)
        return HeartbeatResponse(lastHeartbeat=data.get("lastHeartbeat"))

    async def record_heartbeat(self) -> HeartbeatResponse:
        def _write():
            now_ms = int(time.time() * 1000)
            self._write_json_sync(self._heartbeat_file, {"lastHeartbeat": now_ms})
            return now_ms

        ts = await asyncio.to_thread(_write)
        return HeartbeatResponse(lastHeartbeat=ts)

    # -------------------------------------------------------------------------
    # Models / openclaw.json
    # -------------------------------------------------------------------------

    def _read_openclaw_sync(self) -> dict:
        with _openclaw_lock:
            return self._read_json_sync(self._openclaw_json, {})

    def _write_openclaw_sync(self, data: dict) -> None:
        with _openclaw_lock:
            self._write_json_sync(self._openclaw_json, data)

    async def get_models(self) -> list[str]:
        def _read():
            config = self._read_openclaw_sync()
            primary = (config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary") or "")
            fallbacks = config.get("agents", {}).get("defaults", {}).get("model", {}).get("fallbacks") or []
            models_config = config.get("agents", {}).get("defaults", {}).get("models") or {}
            seen: dict[str, None] = {}
            for m in [primary, *fallbacks, *models_config.keys()]:
                if m:
                    seen[m] = None
            return list(seen.keys())

        return await asyncio.to_thread(_read)

    async def set_model(self, model: str) -> ModelResponse:
        def _write():
            config = self._read_openclaw_sync()
            config.setdefault("agents", {}).setdefault("defaults", {}).setdefault("model", {})
            config["agents"]["defaults"]["model"]["primary"] = model
            self._write_openclaw_sync(config)

        await asyncio.to_thread(_write)
        return ModelResponse(success=True, model=model)

    def _get_active_model_sync(self) -> str:
        config = self._read_openclaw_sync()
        raw = config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "unknown")
        return raw.replace("anthropic/", "")

    # -------------------------------------------------------------------------
    # Usage
    # -------------------------------------------------------------------------

    def _compute_usage_sync(self) -> UsageResponse:
        now = datetime.now(timezone.utc)
        session_window_start = now - timedelta(hours=5)
        week_start = now - timedelta(days=7)

        tokens_session = 0
        tokens_week = 0

        sessions_path = settings.sessions_path
        if not sessions_path.exists():
            model = self._get_active_model_sync()
            return UsageResponse(
                model=model,
                tiers=[
                    UsageTier(label="Current session", percent=0, resetsIn="5h 0m"),
                    UsageTier(label="Current week (all models)", percent=0, resetsIn="7d 0h"),
                ],
            )

        try:
            files = list(sessions_path.glob("*.jsonl"))
            for fp in files:
                try:
                    stat = fp.stat()
                    file_mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    # Skip files too old to contribute to any window
                    if file_mtime < week_start:
                        continue
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                    for line in content.splitlines():
                        if not line.strip():
                            continue
                        try:
                            entry = json.loads(line)
                            usage = entry.get("message", {}).get("usage") or entry.get("usage")
                            if not usage or not usage.get("cost", {}).get("total"):
                                continue
                            tokens = (
                                (usage.get("input") or 0)
                                + (usage.get("output") or 0)
                                + (usage.get("cacheRead") or 0)
                            )
                            ts_raw = entry.get("timestamp")
                            if ts_raw:
                                try:
                                    ts = datetime.fromisoformat(str(ts_raw))
                                    if ts.tzinfo is None:
                                        ts = ts.replace(tzinfo=timezone.utc)
                                except (ValueError, TypeError):
                                    ts = file_mtime
                            else:
                                ts = file_mtime

                            if ts >= week_start:
                                tokens_week += tokens
                            if ts >= session_window_start:
                                tokens_session += tokens
                        except (json.JSONDecodeError, KeyError):
                            continue
                except OSError:
                    continue
        except OSError:
            pass

        session_pct = min(100, round((tokens_session / SESSION_LIMIT) * 100))
        weekly_pct = min(100, round((tokens_week / WEEKLY_LIMIT) * 100))

        # Next session reset: 5h from now (rolling window)
        session_reset_ms = 5 * 3600 * 1000
        weekly_reset_ms = 7 * 24 * 3600 * 1000

        model = self._get_active_model_sync()

        return UsageResponse(
            model=model,
            tiers=[
                UsageTier(
                    label="Current session",
                    percent=session_pct,
                    resetsIn=_format_duration(session_reset_ms),
                ),
                UsageTier(
                    label="Current week (all models)",
                    percent=weekly_pct,
                    resetsIn=_format_duration(weekly_reset_ms),
                ),
            ],
        )

    async def get_usage(self) -> UsageResponse:
        global _usage_cache
        if _usage_cache and time.monotonic() - _usage_cache.computed_at < _USAGE_CACHE_TTL:
            return _usage_cache.result
        result = await asyncio.to_thread(self._compute_usage_sync)
        _usage_cache = _UsageCache(computed_at=time.monotonic(), result=result)
        return result

    # -------------------------------------------------------------------------
    # Skills
    # -------------------------------------------------------------------------

    def _parse_frontmatter(self, content: str) -> dict[str, str]:
        match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", content)
        if not match:
            return {}
        fm: dict[str, str] = {}
        for line in match.group(1).splitlines():
            m = re.match(r"^(\w[\w\s]*?):\s*(.+)$", line)
            if m:
                fm[m.group(1).strip().lower()] = m.group(2).strip().strip("\"'")
        return fm

    def _scan_skills_sync(self) -> list[dict]:
        config = self._read_openclaw_sync()
        entries = (config.get("skills") or {}).get("entries") or {}
        skills: list[dict] = []

        skill_dirs: list[tuple[str, Path]] = []
        if settings.bundled_skills_dir:
            skill_dirs.append(("bundled", Path(settings.bundled_skills_dir)))
        skill_dirs.append(("managed", settings.openclaw_path / "skills"))
        skill_dirs.append(("workspace", settings.workspace_path / "skills"))

        for source, directory in skill_dirs:
            if not directory.exists():
                continue
            try:
                for d in sorted(directory.iterdir()):
                    if not d.is_dir():
                        continue
                    skill_id = d.name
                    md_path = d / "SKILL.md"
                    fm: dict[str, str] = {}
                    has_metadata = False
                    if md_path.exists():
                        try:
                            content = md_path.read_text(encoding="utf-8")
                            fm = self._parse_frontmatter(content)
                            has_metadata = bool(fm)
                        except OSError:
                            pass
                    entry = entries.get(skill_id) or {}
                    enabled = entry.get("enabled", True)
                    if enabled is None:
                        enabled = True
                    skills.append({
                        "id": skill_id,
                        "name": fm.get("name") or skill_id,
                        "description": fm.get("description") or "",
                        "source": source,
                        "enabled": bool(enabled),
                        "path": str(d),
                        "hasMetadata": has_metadata,
                    })
            except OSError:
                continue
        return skills

    async def list_skills(self) -> list[Skill]:
        raw = await asyncio.to_thread(self._scan_skills_sync)
        return [Skill(**s) for s in raw]

    async def toggle_skill(self, skill_id: str, enabled: bool | None) -> Skill | None:
        def _toggle():
            config = self._read_openclaw_sync()
            config.setdefault("skills", {}).setdefault("entries", {})
            current_enabled = (config["skills"]["entries"].get(skill_id) or {}).get("enabled", True)
            new_enabled = (not current_enabled) if enabled is None else enabled
            config["skills"]["entries"][skill_id] = {
                **(config["skills"]["entries"].get(skill_id) or {}),
                "enabled": new_enabled,
            }
            self._write_openclaw_sync(config)
            all_skills = self._scan_skills_sync()
            return next((s for s in all_skills if s["id"] == skill_id), None)

        raw = await asyncio.to_thread(_toggle)
        if raw is None:
            return None
        return Skill(**raw)

    async def create_skill(self, payload: SkillCreate) -> Skill:
        def _create():
            skill_dir = settings.workspace_path / "skills" / payload.name
            skill_dir.mkdir(parents=True, exist_ok=True)
            desc = payload.description or ""
            instructions = payload.instructions or ""
            md = f"---\nname: {payload.name}\ndescription: {desc}\n---\n\n{instructions}"
            (skill_dir / "SKILL.md").write_text(md, encoding="utf-8")
            all_skills = self._scan_skills_sync()
            return next((s for s in all_skills if s["id"] == payload.name and s["source"] == "workspace"), None)

        raw = await asyncio.to_thread(_create)
        if raw is None:
            return Skill(id=payload.name, name=payload.name, source="workspace", path="")
        return Skill(**raw)

    async def get_skill_content(self, skill_id: str) -> str | None:
        def _read():
            all_skills = self._scan_skills_sync()
            skill = next((s for s in all_skills if s["id"] == skill_id), None)
            if not skill:
                return None
            try:
                return (Path(skill["path"]) / "SKILL.md").read_text(encoding="utf-8")
            except OSError:
                return None

        return await asyncio.to_thread(_read)

    async def delete_skill(self, skill_id: str) -> tuple[bool, str | None]:
        def _delete():
            import shutil
            all_skills = self._scan_skills_sync()
            skill = next((s for s in all_skills if s["id"] == skill_id), None)
            if not skill:
                return False, "Not found"
            if skill["source"] != "workspace":
                return False, "Can only delete workspace skills"
            try:
                shutil.rmtree(skill["path"])
                return True, None
            except OSError as e:
                return False, str(e)

        return await asyncio.to_thread(_delete)

    # -------------------------------------------------------------------------
    # Workspace files (SOUL.md, IDENTITY.md, USER.md, AGENTS.md)
    # -------------------------------------------------------------------------

    def _validate_workspace_filename(self, name: str) -> bool:
        return name in _ALLOWED_WORKSPACE_FILES

    async def get_workspace_file(self, name: str) -> WorkspaceFileResponse:
        def _read():
            fp = settings.workspace_path / name
            try:
                content = fp.read_text(encoding="utf-8")
                last_mod = datetime.fromtimestamp(fp.stat().st_mtime, tz=timezone.utc).isoformat()
                return WorkspaceFileResponse(content=content, lastModified=last_mod)
            except OSError:
                return WorkspaceFileResponse(content="", lastModified=None)

        return await asyncio.to_thread(_read)

    async def update_workspace_file(self, name: str, content: str) -> None:
        def _write():
            fp = settings.workspace_path / name
            hist_path = self._history_file(name)
            # Append old content to history before overwriting
            if fp.exists():
                old = fp.read_text(encoding="utf-8")
                if old.strip():
                    history = self._read_json_sync(hist_path, [])
                    history.append({"timestamp": _now_iso(), "content": old})
                    while len(history) > 20:
                        history.pop(0)
                    self._write_json_sync(hist_path, history)
            fp.write_text(content, encoding="utf-8")

        await asyncio.to_thread(_write)

    async def get_file_history(self, name: str) -> list[HistoryEntry]:
        def _read():
            return self._read_json_sync(self._history_file(name), [])

        raw = await asyncio.to_thread(_read)
        return [HistoryEntry(**e) for e in raw]

    async def revert_workspace_file(self, name: str, index: int) -> WorkspaceFileResponse | None:
        def _revert():
            hist_path = self._history_file(name)
            history = self._read_json_sync(hist_path, [])
            if index < 0 or index >= len(history):
                return None
            fp = settings.workspace_path / name
            # Save current before reverting
            if fp.exists():
                old = fp.read_text(encoding="utf-8")
                if old.strip():
                    history.append({"timestamp": _now_iso(), "content": old})
                    while len(history) > 20:
                        history.pop(0)
                    self._write_json_sync(hist_path, history)
            reverted = history[index]["content"]
            fp.write_text(reverted, encoding="utf-8")
            return reverted

        content = await asyncio.to_thread(_revert)
        if content is None:
            return None
        return WorkspaceFileResponse(content=content, lastModified=_now_iso())

    def get_soul_templates(self) -> list[SoulTemplate]:
        return _SOUL_TEMPLATES

    # -------------------------------------------------------------------------
    # Calendar
    # -------------------------------------------------------------------------

    async def get_calendar(self) -> dict[str, CalendarDay]:
        def _build():
            data: dict[str, dict] = {}
            # Memory files
            memory_dir = settings.memory_dir
            date_re = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
            try:
                for f in memory_dir.iterdir():
                    if date_re.match(f.name):
                        date_str = f.stem
                        data.setdefault(date_str, {"memory": False, "tasks": []})
                        data[date_str]["memory"] = True
            except OSError:
                pass
            # Completed tasks
            tasks = self._read_tasks_sync()
            for t in tasks:
                if t.get("completedAt"):
                    date_str = t["completedAt"][:10]
                    data.setdefault(date_str, {"memory": False, "tasks": []})
                    data[date_str]["tasks"].append(t.get("title", ""))
            return data

        raw = await asyncio.to_thread(_build)
        return {k: CalendarDay(**v) for k, v in raw.items()}

    # -------------------------------------------------------------------------
    # Stats (for overview widget)
    # -------------------------------------------------------------------------

    async def get_stats(self) -> WarRoomStats:
        tasks = await asyncio.to_thread(self._read_tasks_sync)
        heartbeat = await self.get_heartbeat()
        model = await asyncio.to_thread(self._get_active_model_sync)

        in_progress = sum(1 for t in tasks if t.get("status") == "in-progress")
        todo = sum(1 for t in tasks if t.get("status") == "todo")

        return WarRoomStats(
            in_progress_count=in_progress,
            todo_count=todo,
            last_heartbeat=heartbeat.lastHeartbeat,
            active_model=model.replace("anthropic/", ""),
        )


warroom_service = WarRoomService()
