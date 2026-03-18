"""Skills browser service — scans skill directories for metadata."""

import datetime
import json
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# Updated source directories with new labels
SKILL_DIRS = [
    ("System", Path("/opt/homebrew/lib/node_modules/openclaw/skills/")),
    ("User", Path("~/.openclaw/skills/").expanduser()),
    ("Workspace", Path("~/.openclaw/workspace/skills/").expanduser()),
    ("Extension", Path("~/.openclaw/extensions/acpx/skills/").expanduser()),
    ("Extension", Path("~/.agents/skills/").expanduser()),
]


class SkillsBrowserService:
    def _parse_frontmatter(self, content: str) -> dict[str, str]:
        """Parse YAML-like frontmatter from SKILL.md.

        Handles simple key: value, quoted values, and YAML folded/literal
        scalars (> and |) with indented continuation lines.
        """
        match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", content)
        if not match:
            return {}
        fm: dict[str, str] = {}
        lines = match.group(1).splitlines()
        i = 0
        while i < len(lines):
            m = re.match(r"^(\w[\w\s]*?):\s*(.*?)\s*$", lines[i])
            if m:
                key = m.group(1).strip().lower()
                val = m.group(2).strip().strip("\"'")
                # Handle YAML folded (>) or literal (|) block scalars
                if val in (">", "|", ">-", "|-"):
                    parts: list[str] = []
                    i += 1
                    while i < len(lines) and (lines[i].startswith("  ") or lines[i].strip() == ""):
                        parts.append(lines[i].strip())
                        i += 1
                    fm[key] = " ".join(p for p in parts if p)
                    continue
                else:
                    fm[key] = val
            i += 1
        return fm

    def scan_all(self) -> list[dict]:
        """Scan all skill directories and return skill metadata."""
        skills: list[dict] = []
        seen: set[str] = set()

        for source, directory in SKILL_DIRS:
            if not directory.exists():
                continue
            for d in sorted(directory.iterdir()):
                if not d.is_dir():
                    continue
                skill_name = d.name
                if skill_name in seen:
                    continue
                seen.add(skill_name)

                md_path = d / "SKILL.md"
                description = ""
                if md_path.exists():
                    try:
                        content = md_path.read_text(encoding="utf-8")
                        fm = self._parse_frontmatter(content)
                        description = fm.get("description", "")
                        # Fallback: first non-empty, non-heading line
                        if not description:
                            for line in content.splitlines():
                                line = line.strip()
                                if line and not line.startswith("#") and not line.startswith("---"):
                                    description = line[:200]
                                    break
                    except OSError:
                        pass

                skills.append(
                    {
                        "name": skill_name,
                        "description": description,
                        "source": source,
                        "source_label": source,
                    }
                )

        return skills

    async def list_from_db(
        self,
        db: AsyncSession,
        source: str | None = None,
        q: str | None = None,
        drifted: bool = False,
    ) -> list[dict]:
        """List skills from the database. Returns empty list if DB has no data."""
        filters = ["removed_at IS NULL"]
        params: dict = {}

        if source:
            filters.append("source_label = :source")
            params["source"] = source
        if q:
            filters.append("(skill_name ILIKE :q OR description ILIKE :q)")
            params["q"] = f"%{q}%"
        if drifted:
            filters.append("last_changed_at IS NOT NULL")

        where = " AND ".join(filters)

        result = await db.execute(
            text(f"""
                SELECT id, skill_name, description, source_label,
                       file_count, sha256_hash, last_indexed_at, last_changed_at
                FROM skills_index
                WHERE {where}
                ORDER BY source_label, skill_name
            """),
            params,
        )

        rows = result.fetchall()
        return [
            {
                "id": row.id,
                "name": row.skill_name,
                "description": row.description or "",
                "source": row.source_label,
                "source_label": row.source_label,
                "file_count": row.file_count,
                "sha256_hash": row.sha256_hash,
                "last_indexed_at": row.last_indexed_at,
                "last_changed_at": row.last_changed_at,
                "has_drift": row.last_changed_at is not None,
            }
            for row in rows
        ]

    async def get_skill_detail_from_db(self, db: AsyncSession, skill_name: str) -> dict | None:
        """Get skill detail enriched with DB data."""
        result = await db.execute(
            text("""
                SELECT sha256_hash, last_changed_at, source_label
                FROM skills_index
                WHERE skill_name = :name AND removed_at IS NULL
                LIMIT 1
            """),
            {"name": skill_name},
        )
        row = result.fetchone()
        if row:
            return {
                "sha256_hash": row.sha256_hash,
                "last_changed_at": row.last_changed_at,
                "source_label": row.source_label,
            }
        return None

    def get_skill_content(self, name: str) -> str | None:
        """Return SKILL.md content for a specific skill."""
        # Guard against path traversal
        if "/" in name or "\\" in name or ".." in name:
            return None
        for _, directory in SKILL_DIRS:
            if not directory.exists():
                continue
            skill_dir = directory / name
            md_path = skill_dir / "SKILL.md"
            if md_path.exists():
                try:
                    return md_path.read_text(encoding="utf-8")
                except OSError:
                    return None
        return None

    async def get_drift_report(
        self,
        db: AsyncSession,
        since: datetime.datetime | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Return recent drift entries joined with skill metadata."""
        if since is None:
            since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)

        result = await db.execute(
            text("""
                SELECT
                    si.skill_name,
                    si.source_label,
                    dl.old_hash,
                    dl.new_hash,
                    dl.old_file_count,
                    dl.new_file_count,
                    dl.files_changed,
                    dl.detected_at
                FROM skills_drift_log dl
                JOIN skills_index si ON si.id = dl.skill_id
                WHERE dl.detected_at >= :since
                ORDER BY dl.detected_at DESC
                LIMIT :limit
            """),
            {"since": since, "limit": limit},
        )

        rows = result.fetchall()
        entries = []
        for row in rows:
            files_changed = row.files_changed
            if isinstance(files_changed, str):
                files_changed = json.loads(files_changed)
            entries.append(
                {
                    "skill_name": row.skill_name,
                    "source_label": row.source_label,
                    "old_hash": row.old_hash,
                    "new_hash": row.new_hash,
                    "old_file_count": row.old_file_count,
                    "new_file_count": row.new_file_count,
                    "files_changed": files_changed,
                    "detected_at": row.detected_at,
                }
            )
        return entries

    async def get_stats(self, db: AsyncSession) -> dict:
        """Return overview statistics for the Skills Hub."""
        # Total skills (exclude soft-deleted)
        total_result = await db.execute(
            text("SELECT COUNT(*) AS cnt FROM skills_index WHERE removed_at IS NULL")
        )
        total_skills = total_result.scalar() or 0

        # By source
        source_result = await db.execute(
            text("""
                SELECT source_label, COUNT(*) AS cnt
                FROM skills_index
                WHERE removed_at IS NULL
                GROUP BY source_label
                ORDER BY source_label
            """)
        )
        by_source = {row.source_label: row.cnt for row in source_result.fetchall()}

        # Drifted in last 7 days
        seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        drift_result = await db.execute(
            text("""
                SELECT COUNT(DISTINCT skill_id) AS cnt
                FROM skills_drift_log
                WHERE detected_at >= :since
            """),
            {"since": seven_days_ago},
        )
        drifted_last_7d = drift_result.scalar() or 0

        # Last full index timestamp
        index_result = await db.execute(
            text("""
                SELECT MAX(last_indexed_at) AS last_idx
                FROM skills_index
                WHERE removed_at IS NULL
            """)
        )
        last_full_index = index_result.scalar()

        return {
            "total_skills": total_skills,
            "by_source": by_source,
            "drifted_last_7d": drifted_last_7d,
            "last_full_index": last_full_index,
        }


skills_browser_service = SkillsBrowserService()
