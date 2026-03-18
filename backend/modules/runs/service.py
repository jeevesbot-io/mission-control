"""Agent Runs service — raw SQL queries against agent_runs table."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import text

from core.database import async_session

from .models import AgentCount, AgentRun, AgentRunCreate, AgentRunList, HeatmapDay

logger = logging.getLogger(__name__)

# All columns in agent_runs (order matters for SELECT *)
_COLUMNS = (
    "id",
    "agent_id",
    "run_type",
    "trigger",
    "status",
    "summary",
    "duration_ms",
    "tokens_used",
    "metadata",
    "prompt_preview",
    "channel",
    "session_key",
    "completed_at",
    "outcome",
    "created_at",
)

_SELECT_COLS = ", ".join(_COLUMNS)


def _row_to_agent_run(row) -> AgentRun:
    """Map a SQLAlchemy Row to an AgentRun model."""
    mapping = row._mapping
    return AgentRun(**{col: mapping[col] for col in _COLUMNS})


class RunsService:
    """Business logic for agent run logging and querying."""

    async def ingest(self, payload: AgentRunCreate) -> AgentRun:
        """Insert a new agent run record."""
        run_id = uuid4()
        now = datetime.now(timezone.utc)

        async with async_session() as session:
            result = await session.execute(
                text(
                    """
                    INSERT INTO agent_runs (
                        id, agent_id, run_type, trigger, status, summary,
                        duration_ms, tokens_used, metadata, prompt_preview,
                        channel, session_key, completed_at, outcome, created_at
                    ) VALUES (
                        :id, :agent_id, :run_type, :trigger, :status, :summary,
                        :duration_ms, :tokens_used, CAST(:metadata AS jsonb), :prompt_preview,
                        :channel, :session_key, :completed_at, :outcome, :created_at
                    )
                    RETURNING {cols}
                """.format(cols=_SELECT_COLS)
                ),
                {
                    "id": run_id,
                    "agent_id": payload.agent_id,
                    "run_type": payload.run_type,
                    "trigger": payload.trigger,
                    "status": payload.status,
                    "summary": payload.summary,
                    "duration_ms": payload.duration_ms,
                    "tokens_used": payload.tokens_used,
                    "metadata": json.dumps(payload.metadata)
                    if payload.metadata is not None
                    else None,
                    "prompt_preview": (payload.prompt_preview or "")[:500]
                    if payload.prompt_preview
                    else None,
                    "channel": payload.channel,
                    "session_key": payload.session_key,
                    "completed_at": now if payload.outcome else None,
                    "outcome": payload.outcome,
                    "created_at": now,
                },
            )
            await session.commit()
            row = result.fetchone()
            return _row_to_agent_run(row)

    async def list_runs(
        self,
        page: int = 1,
        page_size: int = 50,
        agent_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        outcome: str | None = None,
        trigger: str | None = None,
    ) -> AgentRunList:
        """Paginated list with optional filters."""
        conditions: list[str] = []
        params: dict = {}

        if agent_id:
            conditions.append("agent_id = :agent_id")
            params["agent_id"] = agent_id
        if date_from:
            conditions.append("created_at >= :date_from::timestamptz")
            params["date_from"] = date_from
        if date_to:
            conditions.append("created_at < (:date_to::date + interval '1 day')")
            params["date_to"] = date_to
        if outcome:
            conditions.append("outcome = :outcome")
            params["outcome"] = outcome
        if trigger:
            conditions.append("trigger = :trigger")
            params["trigger"] = trigger

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        async with async_session() as session:
            # Count
            count_result = await session.execute(
                text(f"SELECT COUNT(*) FROM agent_runs {where}"), params
            )
            total = count_result.scalar() or 0

            # Fetch page
            result = await session.execute(
                text(f"""
                    SELECT {_SELECT_COLS} FROM agent_runs
                    {where}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                params,
            )
            rows = result.fetchall()

        return AgentRunList(
            items=[_row_to_agent_run(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_run(self, run_id: UUID) -> AgentRun | None:
        """Fetch a single run by ID."""
        async with async_session() as session:
            result = await session.execute(
                text(f"SELECT {_SELECT_COLS} FROM agent_runs WHERE id = :id"),
                {"id": run_id},
            )
            row = result.fetchone()
            return _row_to_agent_run(row) if row else None

    async def get_heatmap(self, year: int) -> list[HeatmapDay]:
        """Daily run counts grouped by date and agent_id for a given year."""
        async with async_session() as session:
            result = await session.execute(
                text("""
                    SELECT
                        created_at::date AS day,
                        agent_id,
                        COUNT(*) AS cnt
                    FROM agent_runs
                    WHERE EXTRACT(YEAR FROM created_at) = :year
                    GROUP BY day, agent_id
                    ORDER BY day
                """),
                {"year": year},
            )
            rows = result.fetchall()

        # Aggregate into HeatmapDay objects
        days: dict[str, HeatmapDay] = {}
        for row in rows:
            mapping = row._mapping
            day_str = str(mapping["day"])
            agent = mapping["agent_id"]
            cnt = mapping["cnt"]

            if day_str not in days:
                days[day_str] = HeatmapDay(date=day_str, count=0, agents=[])
            days[day_str].count += cnt
            days[day_str].agents.append(AgentCount(agent_id=agent, count=cnt))

        return list(days.values())

    async def get_day_runs(self, date: str, agent_id: str | None = None) -> list[AgentRun]:
        """All runs for a specific day, optionally filtered by agent."""
        from datetime import date as date_type

        parsed_date = date_type.fromisoformat(date)
        conditions = ["created_at::date = :date"]
        params: dict = {"date": parsed_date}

        if agent_id:
            conditions.append("agent_id = :agent_id")
            params["agent_id"] = agent_id

        where = "WHERE " + " AND ".join(conditions)

        async with async_session() as session:
            result = await session.execute(
                text(f"""
                    SELECT {_SELECT_COLS} FROM agent_runs
                    {where}
                    ORDER BY created_at DESC
                """),
                params,
            )
            rows = result.fetchall()

        return [_row_to_agent_run(r) for r in rows]

    async def get_agent_timeline(
        self, agent_id: str, page: int = 1, page_size: int = 50
    ) -> AgentRunList:
        """Paginated run history for a single agent."""
        offset = (page - 1) * page_size

        async with async_session() as session:
            count_result = await session.execute(
                text("SELECT COUNT(*) FROM agent_runs WHERE agent_id = :agent_id"),
                {"agent_id": agent_id},
            )
            total = count_result.scalar() or 0

            result = await session.execute(
                text(f"""
                    SELECT {_SELECT_COLS} FROM agent_runs
                    WHERE agent_id = :agent_id
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {"agent_id": agent_id, "limit": page_size, "offset": offset},
            )
            rows = result.fetchall()

        return AgentRunList(
            items=[_row_to_agent_run(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )


runs_service = RunsService()
