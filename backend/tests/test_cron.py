"""Tests for the Cron Monitor module."""

import time
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app
from modules.cron.models import (
    ChannelLoad,
    CronDelivery,
    CronHealthSummary,
    CronJob,
    CronSchedule,
    CronState,
)
from modules.cron.service import (
    _compute_health,
    _estimate_interval_minutes,
    _parse_job,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Module registration
# ---------------------------------------------------------------------------


def test_modules_includes_cron():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "cron" in ids


# ---------------------------------------------------------------------------
# Interval estimation heuristic
# ---------------------------------------------------------------------------


def test_interval_every_minute():
    assert _estimate_interval_minutes("* * * * *") == 1.0


def test_interval_every_n_minutes():
    assert _estimate_interval_minutes("*/5 * * * *") == 5.0
    assert _estimate_interval_minutes("*/15 * * * *") == 15.0


def test_interval_hourly():
    assert _estimate_interval_minutes("0 * * * *") == 60.0


def test_interval_every_n_hours():
    assert _estimate_interval_minutes("0 */2 * * *") == 120.0
    assert _estimate_interval_minutes("0 */6 * * *") == 360.0


def test_interval_daily():
    assert _estimate_interval_minutes("0 7 * * *") == 24 * 60


def test_interval_weekly():
    assert _estimate_interval_minutes("0 7 * * 1") == 7 * 24 * 60


def test_interval_monthly():
    assert _estimate_interval_minutes("0 9 1 * *") == 30 * 24 * 60


def test_interval_fallback_short_expr():
    # Malformed expression should fall back to 24 hours
    assert _estimate_interval_minutes("bad") == 24 * 60


# ---------------------------------------------------------------------------
# Health computation
# ---------------------------------------------------------------------------


def _state(last_run_ms: int | None = None) -> CronState:
    return CronState(lastRunAtMs=last_run_ms)


def test_health_disabled():
    assert _compute_health(False, _state(int(time.time() * 1000)), 60) == "disabled"


def test_health_never_run():
    assert _compute_health(True, _state(None), 60) == "never"


def test_health_ok():
    # Last run 30 minutes ago, interval is 60 min → within 2x → ok
    last_run = int(time.time() * 1000) - 30 * 60 * 1000
    assert _compute_health(True, _state(last_run), 60) == "ok"


def test_health_late():
    # Last run 150 minutes ago, interval is 60 min → >2x but <4x → late
    last_run = int(time.time() * 1000) - 150 * 60 * 1000
    assert _compute_health(True, _state(last_run), 60) == "late"


def test_health_failing():
    # Last run 300 minutes ago, interval is 60 min → >4x → failing
    last_run = int(time.time() * 1000) - 300 * 60 * 1000
    assert _compute_health(True, _state(last_run), 60) == "failing"


# ---------------------------------------------------------------------------
# Job parsing
# ---------------------------------------------------------------------------


def _make_raw_job(
    *,
    enabled: bool = True,
    expr: str = "0 7 * * *",
    last_run_ms: int | None = None,
    delivery_mode: str = "none",
    channel: str = "",
    to: str = "",
) -> dict:
    return {
        "id": "test-id",
        "agentId": "main",
        "name": "Test Job",
        "enabled": enabled,
        "schedule": {"kind": "cron", "expr": expr, "tz": "Europe/London"},
        "delivery": {"mode": delivery_mode, "channel": channel, "to": to},
        "state": {
            "lastRunAtMs": last_run_ms,
            "lastStatus": "ok" if last_run_ms else "never",
        },
    }


def test_parse_job_basic():
    now_ms = int(time.time() * 1000)
    job = _parse_job(_make_raw_job(last_run_ms=now_ms))
    assert job.id == "test-id"
    assert job.name == "Test Job"
    assert job.enabled is True
    assert job.health == "ok"


def test_parse_job_disabled():
    job = _parse_job(_make_raw_job(enabled=False, last_run_ms=int(time.time() * 1000)))
    assert job.health == "disabled"


# ---------------------------------------------------------------------------
# Router: GET /api/cron/schedule
# ---------------------------------------------------------------------------


def test_list_jobs():
    now_ms = int(time.time() * 1000)
    mock_jobs = [
        CronJob(
            id="j1",
            agentId="main",
            name="Job One",
            enabled=True,
            schedule=CronSchedule(expr="0 7 * * *"),
            delivery=CronDelivery(),
            state=CronState(lastRunAtMs=now_ms),
            health="ok",
        ),
        CronJob(
            id="j2",
            agentId="main",
            name="Job Two",
            enabled=False,
            schedule=CronSchedule(expr="0 9 * * *"),
            delivery=CronDelivery(),
            state=CronState(),
            health="disabled",
        ),
    ]
    with patch("modules.cron.service.list_jobs", new_callable=AsyncMock) as mock:
        mock.return_value = mock_jobs
        response = client.get("/api/cron/schedule")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Job One"
        assert data[0]["health"] == "ok"
        assert data[1]["health"] == "disabled"


# ---------------------------------------------------------------------------
# Router: GET /api/cron/health
# ---------------------------------------------------------------------------


def test_health_summary():
    summary = CronHealthSummary(
        total=35, enabled=26, ok=20, late=3, failing=1, never_run=2
    )
    with patch(
        "modules.cron.service.get_health_summary", new_callable=AsyncMock
    ) as mock:
        mock.return_value = summary
        response = client.get("/api/cron/health")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 35
        assert data["enabled"] == 26
        assert data["ok"] == 20
        assert data["late"] == 3
        assert data["failing"] == 1
        assert data["never_run"] == 2


# ---------------------------------------------------------------------------
# Router: GET /api/cron/channels
# ---------------------------------------------------------------------------


def test_channel_load():
    channels = [
        ChannelLoad(channel="slack:#briefing", jobs_count=5, msgs_per_day=5.0),
        ChannelLoad(channel="slack:#alerts", jobs_count=3, msgs_per_day=72.0),
    ]
    with patch(
        "modules.cron.service.list_channel_load", new_callable=AsyncMock
    ) as mock:
        mock.return_value = channels
        response = client.get("/api/cron/channels")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["channel"] == "slack:#briefing"
        assert data[1]["msgs_per_day"] == 72.0


# ---------------------------------------------------------------------------
# Service integration: loading from jobs.json
# ---------------------------------------------------------------------------


def _mock_jobs_json(jobs: list[dict]) -> dict:
    return {"version": 1, "jobs": jobs}


def test_load_jobs_correct_count():
    """Loading 3 jobs from a mocked file returns 3 CronJob instances."""
    now_ms = int(time.time() * 1000)
    raw = _mock_jobs_json([
        _make_raw_job(last_run_ms=now_ms),
        _make_raw_job(enabled=False),
        _make_raw_job(last_run_ms=None),
    ])

    with patch("modules.cron.service._read_json_sync", return_value=raw):
        from modules.cron.service import _load_jobs_sync

        jobs = _load_jobs_sync()
        assert len(jobs) == 3


def test_load_jobs_health_values():
    """Verify health labels for ok, disabled, and never-run jobs."""
    now_ms = int(time.time() * 1000)
    raw = _mock_jobs_json([
        _make_raw_job(last_run_ms=now_ms),          # ok
        _make_raw_job(enabled=False),                # disabled
        _make_raw_job(last_run_ms=None),             # never
    ])

    with patch("modules.cron.service._read_json_sync", return_value=raw):
        from modules.cron.service import _load_jobs_sync

        jobs = _load_jobs_sync()
        assert jobs[0].health == "ok"
        assert jobs[1].health == "disabled"
        assert jobs[2].health == "never"


def test_health_summary_from_jobs():
    """get_health_summary aggregates counts correctly."""
    now_ms = int(time.time() * 1000)
    # For a daily job (interval=1440 min), >4x interval = >5760 min = >96h
    old_ms = now_ms - 100 * 60 * 60 * 1000  # 100 hours ago → failing for daily job

    raw = _mock_jobs_json([
        _make_raw_job(last_run_ms=now_ms),           # ok
        _make_raw_job(last_run_ms=now_ms),           # ok
        _make_raw_job(enabled=False),                # disabled (not counted in enabled)
        _make_raw_job(last_run_ms=None),             # never
        _make_raw_job(last_run_ms=old_ms),           # failing
    ])

    with patch("modules.cron.service._read_json_sync", return_value=raw):
        from modules.cron.service import _load_jobs_sync

        jobs = _load_jobs_sync()
        enabled = [j for j in jobs if j.enabled]
        assert len(jobs) == 5
        assert len(enabled) == 4
        assert sum(1 for j in enabled if j.health == "ok") == 2
        assert sum(1 for j in enabled if j.health == "failing") == 1
        assert sum(1 for j in enabled if j.health == "never") == 1


def test_channel_load_aggregation():
    """Channel load groups by delivery target and sums msgs_per_day."""
    now_ms = int(time.time() * 1000)
    raw = _mock_jobs_json([
        _make_raw_job(
            last_run_ms=now_ms,
            delivery_mode="slack",
            channel="slack",
            to="#briefing",
            expr="0 7 * * *",  # daily → 1 msg/day
        ),
        _make_raw_job(
            last_run_ms=now_ms,
            delivery_mode="slack",
            channel="slack",
            to="#briefing",
            expr="0 7 * * *",  # daily → 1 msg/day
        ),
        _make_raw_job(
            last_run_ms=now_ms,
            delivery_mode="slack",
            channel="slack",
            to="#alerts",
            expr="0 * * * *",  # hourly → 24 msgs/day
        ),
        _make_raw_job(
            last_run_ms=now_ms,
            delivery_mode="none",
            channel="",
            to="",
            expr="0 7 * * *",  # no delivery
        ),
    ])

    with patch("modules.cron.service._read_json_sync", return_value=raw):
        from modules.cron.service import list_channel_load
        import asyncio

        result = asyncio.run(list_channel_load())

        by_channel = {r.channel: r for r in result}

        assert "slack:#briefing" in by_channel
        assert by_channel["slack:#briefing"].jobs_count == 2
        assert by_channel["slack:#briefing"].msgs_per_day == 2.0

        assert "slack:#alerts" in by_channel
        assert by_channel["slack:#alerts"].jobs_count == 1
        assert by_channel["slack:#alerts"].msgs_per_day == 24.0

        assert "(no delivery)" in by_channel
        assert by_channel["(no delivery)"].jobs_count == 1


def test_load_jobs_missing_file():
    """When jobs.json is missing, return an empty list."""
    with patch(
        "modules.cron.service._read_json_sync", return_value={"jobs": []}
    ):
        from modules.cron.service import _load_jobs_sync

        jobs = _load_jobs_sync()
        assert jobs == []


def test_disabled_jobs_excluded_from_channel_load():
    """Disabled jobs should not contribute to channel load."""
    raw = _mock_jobs_json([
        _make_raw_job(
            enabled=False,
            delivery_mode="slack",
            channel="slack",
            to="#briefing",
            expr="0 7 * * *",
        ),
    ])

    with patch("modules.cron.service._read_json_sync", return_value=raw):
        import asyncio

        from modules.cron.service import list_channel_load

        result = asyncio.run(list_channel_load())
        assert result == []
