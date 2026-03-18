"""Cron Monitor module Pydantic models."""

from pydantic import BaseModel


class CronSchedule(BaseModel):
    kind: str = "cron"
    expr: str
    tz: str = "UTC"


class CronDelivery(BaseModel):
    mode: str = "none"
    channel: str = ""
    to: str = ""


class CronState(BaseModel):
    nextRunAtMs: int | None = None
    lastRunAtMs: int | None = None
    lastStatus: str = "never"
    lastDurationMs: int | None = None
    consecutiveErrors: int = 0


class CronJob(BaseModel):
    id: str
    agentId: str
    name: str
    enabled: bool
    schedule: CronSchedule
    delivery: CronDelivery
    state: CronState
    health: str = "unknown"  # ok / late / failing / never / disabled


class CronHealthSummary(BaseModel):
    total: int
    enabled: int
    ok: int
    late: int
    failing: int
    never_run: int


class ChannelLoad(BaseModel):
    channel: str
    jobs_count: int
    msgs_per_day: float  # estimated from cron expressions
