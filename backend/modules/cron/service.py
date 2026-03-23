"""Cron Monitor module service — reads jobs.json and computes health status."""

import asyncio
import json
import re
import threading
import time
from collections import defaultdict
from pathlib import Path

from core.config import settings

from .models import (
    ChannelLoad,
    CronDelivery,
    CronHealthSummary,
    CronJob,
    CronSchedule,
    CronState,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_cron_lock = threading.Lock()


def _read_json_sync(path: Path, default):
    """Read a JSON file synchronously, returning *default* on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _estimate_interval_minutes(expr: str) -> float:
    """Estimate the interval (in minutes) between runs from a cron expression.

    Uses simple heuristics — no cron parsing library required.

    Patterns recognised (fields: minute hour day-of-month month day-of-week):
      * * * * *           → 1 min
      */N * * * *         → N min
      0 * * * *           → 60 min  (hourly)
      0 */N * * *         → N * 60 min  (every N hours)
      0 H * * *           → 24 h  (daily at a fixed hour)
      0 H * * D           → 7 days  (weekly — day-of-week specified)
      0 H D * *           → 30 days (monthly — day-of-month specified)
      fallback            → 24 h
    """
    parts = expr.strip().split()
    if len(parts) < 5:
        return 24 * 60  # fallback

    minute, hour, dom, month, dow = parts[:5]

    # Every-minute: * * * * *
    if minute == "*" and hour == "*":
        return 1.0

    # Every-N-minutes: */N * * * *
    m = re.match(r"^\*/(\d+)$", minute)
    if m and hour == "*":
        return float(m.group(1))

    # Hourly: 0 * * * *
    if hour == "*":
        return 60.0

    # Every-N-hours: 0 */N * * *
    m = re.match(r"^\*/(\d+)$", hour)
    if m:
        return float(m.group(1)) * 60

    # Fixed hour — check if weekly or monthly
    # Weekly: day-of-week is not * (e.g. "0 7 * * 1")
    if dow != "*" and dom == "*":
        return 7 * 24 * 60  # weekly

    # Monthly: day-of-month is not * (e.g. "0 9 1 * *")
    if dom != "*":
        return 30 * 24 * 60  # monthly

    # Daily (fixed hour, no specific dom/dow)
    return 24 * 60


def _compute_health(enabled: bool, state: CronState, interval_min: float) -> str:
    """Derive a health label from the job's enabled flag, run state, and interval."""
    if not enabled:
        return "disabled"
    if state.lastRunAtMs is None:
        return "never"

    now_ms = int(time.time() * 1000)
    age_ms = now_ms - state.lastRunAtMs
    interval_ms = interval_min * 60 * 1000

    if age_ms > 4 * interval_ms:
        return "failing"
    if age_ms > 2 * interval_ms:
        return "late"
    return "ok"


def _parse_job(raw: dict) -> CronJob:
    """Parse a raw job dict from jobs.json into a CronJob model with health."""
    schedule = CronSchedule(**(raw.get("schedule") or {}))
    delivery = CronDelivery(**(raw.get("delivery") or {}))
    state = CronState(**(raw.get("state") or {}))
    enabled = raw.get("enabled", False)
    interval_min = _estimate_interval_minutes(schedule.expr)
    health = _compute_health(enabled, state, interval_min)

    return CronJob(
        id=raw["id"],
        agentId=raw.get("agentId", ""),
        name=raw.get("name", ""),
        enabled=enabled,
        schedule=schedule,
        delivery=delivery,
        state=state,
        health=health,
    )


def _load_jobs_sync() -> list[CronJob]:
    """Read and parse all jobs from the jobs.json file."""
    jobs_path = settings.openclaw_path / "cron" / "jobs.json"
    with _cron_lock:
        data = _read_json_sync(jobs_path, {"jobs": []})
    raw_jobs = data.get("jobs", [])
    return [_parse_job(j) for j in raw_jobs]


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------


async def list_jobs() -> list[CronJob]:
    """Return all cron jobs enriched with health status."""
    return await asyncio.to_thread(_load_jobs_sync)


async def get_health_summary() -> CronHealthSummary:
    """Return aggregate health counts across all jobs."""
    jobs = await asyncio.to_thread(_load_jobs_sync)
    enabled_jobs = [j for j in jobs if j.enabled]
    return CronHealthSummary(
        total=len(jobs),
        enabled=len(enabled_jobs),
        ok=sum(1 for j in enabled_jobs if j.health == "ok"),
        late=sum(1 for j in enabled_jobs if j.health == "late"),
        failing=sum(1 for j in enabled_jobs if j.health == "failing"),
        never_run=sum(1 for j in enabled_jobs if j.health == "never"),
    )


async def list_channel_load() -> list[ChannelLoad]:
    """Return estimated message load per delivery channel."""
    jobs = await asyncio.to_thread(_load_jobs_sync)

    channel_agg: dict[str, dict] = defaultdict(lambda: {"jobs_count": 0, "msgs_per_day": 0.0})

    for job in jobs:
        if not job.enabled:
            continue
        # Build a channel key from delivery target
        if job.delivery.mode == "none" or not job.delivery.to:
            key = "(no delivery)"
        else:
            key = f"{job.delivery.channel}:{job.delivery.to}"

        interval_min = _estimate_interval_minutes(job.schedule.expr)
        msgs_per_day = (24 * 60) / interval_min if interval_min > 0 else 0

        channel_agg[key]["jobs_count"] += 1
        channel_agg[key]["msgs_per_day"] += msgs_per_day

    result = [
        ChannelLoad(
            channel=ch,
            jobs_count=agg["jobs_count"],
            msgs_per_day=round(agg["msgs_per_day"], 2),
        )
        for ch, agg in sorted(channel_agg.items())
    ]
    return result
