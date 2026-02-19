"""Activity module service — JSON file-backed event log."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from core.config import settings
from core.websocket import manager

from .models import ActivityEvent, ActivityFeedResponse, ActivityLogRequest, ActivityStats

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_MAX_EVENTS = 1000


class ActivityService:
    """Activity event log backed by a JSON file."""

    @property
    def _data_file(self) -> Path:
        return settings.dashboard_data_path / "activity.json"

    def _read_sync(self) -> list[dict]:
        with _lock:
            try:
                return json.loads(self._data_file.read_text(encoding="utf-8"))
            except Exception:
                return []

    def _write_sync(self, events: list[dict]) -> None:
        with _lock:
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            self._data_file.write_text(json.dumps(events, indent=2), encoding="utf-8")

    def _append_sync(self, event: dict) -> None:
        events = self._read_sync()
        events.insert(0, event)
        if len(events) > _MAX_EVENTS:
            events = events[:_MAX_EVENTS]
        with _lock:
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            self._data_file.write_text(json.dumps(events, indent=2), encoding="utf-8")

    async def log_event(self, req: ActivityLogRequest) -> ActivityEvent:
        """Log a new activity event and return it."""
        event = ActivityEvent(
            id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            actor=req.actor,
            action=req.action,
            resource_type=req.resource_type,
            resource_id=req.resource_id,
            resource_name=req.resource_name,
            details=req.details,
            module=req.module,
        )
        await asyncio.to_thread(self._append_sync, event.model_dump(mode="json"))
        try:
            await manager.broadcast("activity:new", event.model_dump(mode="json"))
        except Exception:
            pass  # Don't fail event logging if broadcast fails
        return event

    async def get_feed(
        self,
        limit: int = 50,
        cursor: str | None = None,
        module: str | None = None,
        actor: str | None = None,
        action: str | None = None,
    ) -> ActivityFeedResponse:
        """Return paginated activity feed with optional filters."""
        raw = await asyncio.to_thread(self._read_sync)

        # Apply filters
        filtered = raw
        if module:
            filtered = [e for e in filtered if e.get("module") == module]
        if actor:
            filtered = [e for e in filtered if e.get("actor") == actor]
        if action:
            filtered = [e for e in filtered if e.get("action", "").startswith(action)]

        # Apply cursor (events before the cursor timestamp)
        if cursor:
            filtered = [e for e in filtered if e.get("timestamp", "") < cursor]

        total = len(filtered)
        page = filtered[:limit]

        next_cursor = None
        if page:
            next_cursor = page[-1].get("timestamp")

        events = [ActivityEvent(**e) for e in page]
        return ActivityFeedResponse(events=events, total=total, cursor=next_cursor)

    async def get_stats(self) -> ActivityStats:
        """Return activity statistics."""
        raw = await asyncio.to_thread(self._read_sync)

        by_module: dict[str, int] = {}
        by_action: dict[str, int] = {}
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        last_24h = 0

        for e in raw:
            mod = e.get("module", "unknown")
            by_module[mod] = by_module.get(mod, 0) + 1

            act = e.get("action", "unknown")
            by_action[act] = by_action.get(act, 0) + 1

            if e.get("timestamp", "") >= cutoff:
                last_24h += 1

        return ActivityStats(
            total_events=len(raw),
            by_module=by_module,
            by_action=by_action,
            last_24h=last_24h,
        )


activity_service = ActivityService()
