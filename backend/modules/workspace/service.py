"""Workspace module service — file I/O based business logic."""

import asyncio
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.config import settings

from .models import (
    HeartbeatResponse,
    HistoryEntry,
    ModelResponse,
    SoulTemplate,
    UsageResponse,
    UsageTier,
    WorkspaceFileResponse,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_heartbeat_lock = threading.Lock()
_openclaw_lock = threading.Lock()


def _read_json_sync(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json_sync(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------


async def get_heartbeat() -> HeartbeatResponse:
    def _read():
        with _heartbeat_lock:
            data = _read_json_sync(
                settings.dashboard_data_path / "heartbeat.json",
                {"lastHeartbeat": None},
            )
        return HeartbeatResponse(lastHeartbeat=data.get("lastHeartbeat"))

    return await asyncio.to_thread(_read)


async def record_heartbeat() -> HeartbeatResponse:
    def _write():
        now_ms = int(time.time() * 1000)
        with _heartbeat_lock:
            _write_json_sync(
                settings.dashboard_data_path / "heartbeat.json",
                {"lastHeartbeat": now_ms},
            )
        return now_ms

    ts = await asyncio.to_thread(_write)
    return HeartbeatResponse(lastHeartbeat=ts)


# ---------------------------------------------------------------------------
# Usage (reads OpenClaw session JSONL files)
# ---------------------------------------------------------------------------

SESSION_LIMIT = 45_000_000  # ~45M tokens per 5h session window
WEEKLY_LIMIT = 180_000_000  # ~180M tokens per week


@dataclass
class _UsageCache:
    computed_at: float
    result: UsageResponse


_usage_cache: _UsageCache | None = None
_USAGE_CACHE_TTL = 60  # seconds


def _format_duration(ms: float) -> str:
    total_s = max(0, ms / 1000)
    total_m = int(total_s / 60)
    h = total_m // 60
    m = total_m % 60
    d = h // 24
    if d > 0:
        return f"{d}d {h % 24}h"
    return f"{h}h {m}m"


def _get_active_model_sync() -> str:
    _openclaw_json = settings.openclaw_path / "openclaw.json"
    try:
        config = json.loads(_openclaw_json.read_text(encoding="utf-8"))
    except Exception:
        config = {}
    raw = config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "unknown")
    return raw.replace("anthropic/", "")


def _compute_usage_sync() -> UsageResponse:
    now = datetime.now(timezone.utc)
    session_window_start = now - timedelta(hours=5)
    week_start = now - timedelta(days=7)
    tokens_session = 0
    tokens_week = 0
    sessions_path = settings.sessions_path
    if not sessions_path.exists():
        model = _get_active_model_sync()
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
    session_reset_ms = 5 * 3600 * 1000
    weekly_reset_ms = 7 * 24 * 3600 * 1000
    model = _get_active_model_sync()
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


async def get_usage() -> UsageResponse:
    global _usage_cache
    if _usage_cache and time.monotonic() - _usage_cache.computed_at < _USAGE_CACHE_TTL:
        return _usage_cache.result
    result = await asyncio.to_thread(_compute_usage_sync)
    _usage_cache = _UsageCache(computed_at=time.monotonic(), result=result)
    return result


# ---------------------------------------------------------------------------
# Models (OpenClaw config)
# ---------------------------------------------------------------------------


async def get_models() -> list[str]:
    def _read():
        _openclaw_json = settings.openclaw_path / "openclaw.json"
        with _openclaw_lock:
            try:
                config = json.loads(_openclaw_json.read_text(encoding="utf-8"))
            except Exception:
                config = {}
        primary = config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary") or ""
        fallbacks = (
            config.get("agents", {}).get("defaults", {}).get("model", {}).get("fallbacks") or []
        )
        models_config = config.get("agents", {}).get("defaults", {}).get("models") or {}
        seen: dict[str, None] = {}
        for m in [primary, *fallbacks, *models_config.keys()]:
            if m:
                seen[m] = None
        return list(seen.keys())

    return await asyncio.to_thread(_read)


async def set_model(model: str) -> ModelResponse:
    def _write():
        _openclaw_json = settings.openclaw_path / "openclaw.json"
        with _openclaw_lock:
            try:
                config = json.loads(_openclaw_json.read_text(encoding="utf-8"))
            except Exception:
                config = {}
            config.setdefault("agents", {}).setdefault("defaults", {}).setdefault("model", {})
            config["agents"]["defaults"]["model"]["primary"] = model
            _openclaw_json.parent.mkdir(parents=True, exist_ok=True)
            _openclaw_json.write_text(json.dumps(config, indent=2), encoding="utf-8")

    await asyncio.to_thread(_write)
    return ModelResponse(success=True, model=model)


# ---------------------------------------------------------------------------
# Workspace files (SOUL.md, IDENTITY.md, USER.md, AGENTS.md)
# ---------------------------------------------------------------------------

_ALLOWED_WORKSPACE_FILES = {"SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_workspace_filename(name: str) -> bool:
    return name in _ALLOWED_WORKSPACE_FILES


async def get_workspace_file(name: str) -> WorkspaceFileResponse:
    def _read():
        fp = settings.workspace_path / name
        try:
            content = fp.read_text(encoding="utf-8")
            last_mod = datetime.fromtimestamp(fp.stat().st_mtime, tz=timezone.utc).isoformat()
            return WorkspaceFileResponse(content=content, lastModified=last_mod)
        except OSError:
            return WorkspaceFileResponse(content="", lastModified=None)

    return await asyncio.to_thread(_read)


async def update_workspace_file(name: str, content: str) -> None:
    def _write():
        fp = settings.workspace_path / name
        hist_path = settings.dashboard_data_path / f"{name}-history.json"
        if fp.exists():
            old = fp.read_text(encoding="utf-8")
            if old.strip():
                history = _read_json_sync(hist_path, [])
                history.append({"timestamp": _now_iso(), "content": old})
                while len(history) > 20:
                    history.pop(0)
                _write_json_sync(hist_path, history)
        fp.write_text(content, encoding="utf-8")

    await asyncio.to_thread(_write)


async def get_file_history(name: str) -> list[HistoryEntry]:
    def _read():
        return _read_json_sync(settings.dashboard_data_path / f"{name}-history.json", [])

    raw = await asyncio.to_thread(_read)
    return [HistoryEntry(**e) for e in raw]


async def revert_workspace_file(name: str, index: int) -> WorkspaceFileResponse | None:
    def _revert():
        hist_path = settings.dashboard_data_path / f"{name}-history.json"
        history = _read_json_sync(hist_path, [])
        if index < 0 or index >= len(history):
            return None
        fp = settings.workspace_path / name
        if fp.exists():
            old = fp.read_text(encoding="utf-8")
            if old.strip():
                history.append({"timestamp": _now_iso(), "content": old})
                while len(history) > 20:
                    history.pop(0)
                _write_json_sync(hist_path, history)
        reverted = history[index]["content"]
        fp.write_text(reverted, encoding="utf-8")
        return reverted

    content = await asyncio.to_thread(_revert)
    if content is None:
        return None
    return WorkspaceFileResponse(content=content, lastModified=_now_iso())


# ---------------------------------------------------------------------------
# Soul templates
# ---------------------------------------------------------------------------

_SOUL_TEMPLATES = [
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
            "You're warm, friendly, and genuinely care about helping. "
            "Use emoji naturally (not excessively). Be conversational "
            "\u2014 talk like a smart friend, not a manual. Have opinions, "
            "crack jokes when appropriate, and remember: helpfulness > formality."
        ),
    ),
    SoulTemplate(
        name="Technical Expert",
        description="Precise, detailed, code-focused",
        content=(
            "# SOUL.md - Who You Are\n"
            "You are a senior technical consultant. Be precise, thorough, "
            "and opinionated about best practices. Prefer code examples over "
            "explanations. Flag anti-patterns when you see them. Don't sugarcoat "
            "\u2014 if something is wrong, say so directly. Efficiency matters."
        ),
    ),
    SoulTemplate(
        name="Creative Partner",
        description="Imaginative, brainstormy, enthusiastic",
        content=(
            "# SOUL.md - Who You Are\n"
            "You're a creative collaborator \u2014 curious, imaginative, and "
            "always looking for unexpected angles. Brainstorm freely. Suggest "
            "wild ideas alongside safe ones. Get excited about good concepts. "
            "Push creative boundaries while staying grounded in what's achievable."
        ),
    ),
    SoulTemplate(
        name="Stern Operator",
        description="No-nonsense, military-efficient, dry humor",
        content=(
            "# SOUL.md - Who You Are\n"
            "Mission first. Be direct, efficient, and zero-waste in communication. "
            "No pleasantries unless earned. Dry humor is acceptable. Report status "
            "clearly. Flag risks immediately. You don't ask permission for routine "
            "ops \u2014 you execute and report. Save the small talk for after the "
            "job's done."
        ),
    ),
    SoulTemplate(
        name="Sarcastic Sidekick",
        description="Witty, slightly snarky, still helpful",
        content=(
            "# SOUL.md - Who You Are\n"
            "You're helpful, but you're not going to pretend everything is sunshine "
            "and rainbows. Deliver assistance with a side of wit. Be sarcastic when "
            "it's funny, never when it's cruel. You still get the job done \u2014 "
            "you just have commentary while doing it. Think dry British humor meets "
            "competent engineer."
        ),
    ),
]


def get_soul_templates() -> list[SoulTemplate]:
    return _SOUL_TEMPLATES
