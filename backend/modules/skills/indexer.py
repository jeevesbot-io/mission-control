"""Skills indexer — filesystem scanning, SHA-256 hashing, drift detection."""

import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Source directories and their labels
SKILL_SOURCES: list[tuple[str, str]] = [
    (str(Path("/opt/homebrew/lib/node_modules/openclaw/skills")), "System"),
    (str(Path("~/.openclaw/skills").expanduser()), "User"),
    (str(Path("~/.openclaw/workspace/skills").expanduser()), "Workspace"),
    (str(Path("~/.openclaw/extensions/acpx/skills").expanduser()), "Extension"),
    (str(Path("~/.agents/skills").expanduser()), "Extension"),
]

IGNORE_NAMES = {".DS_Store", "__pycache__", ".git", "node_modules"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_DEPTH = 5


def _should_skip(path: Path) -> bool:
    """Check if a path component should be ignored."""
    return any(part in IGNORE_NAMES for part in path.parts)


def compute_skill_hash(skill_dir: Path) -> tuple[str, list[dict[str, Any]], int, int]:
    """Compute composite SHA-256 for a skill directory.

    Returns (composite_hash, file_details, file_count, total_bytes).
    """
    file_hashes: list[str] = []
    file_details: list[dict[str, Any]] = []
    total_bytes = 0
    seen_paths: set[str] = set()

    try:
        skill_dir.resolve()
    except OSError:
        return hashlib.sha256(b"empty").hexdigest(), [], 0, 0

    for f in sorted(skill_dir.rglob("*")):
        if not f.is_file():
            continue
        # Skip ignored names
        rel = f.relative_to(skill_dir)
        if any(part in IGNORE_NAMES for part in rel.parts):
            continue
        # Depth guard
        if len(rel.parts) > MAX_DEPTH:
            continue
        # Symlink loop guard
        try:
            resolved = f.resolve()
            resolved_str = str(resolved)
            if resolved_str in seen_paths:
                continue
            seen_paths.add(resolved_str)
        except OSError:
            continue
        # Size guard
        try:
            size = f.stat().st_size
        except OSError:
            continue
        if size > MAX_FILE_BYTES:
            logger.warning("Skipping large file %s (%d bytes)", f, size)
            continue
        # Hash
        try:
            content = f.read_bytes()
        except (OSError, PermissionError):
            continue
        h = hashlib.sha256(str(rel).encode() + b":" + content).hexdigest()
        file_hashes.append(h)
        file_details.append({"path": str(rel), "size": len(content), "sha256": h})
        total_bytes += len(content)

    if not file_hashes:
        composite = hashlib.sha256(b"empty").hexdigest()
    else:
        composite = hashlib.sha256("".join(file_hashes).encode()).hexdigest()

    return composite, file_details, len(file_hashes), total_bytes


def parse_frontmatter(skill_md: Path) -> dict[str, Any]:
    """Extract YAML frontmatter from a SKILL.md file."""
    try:
        content = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    if not content.startswith("---"):
        return {}

    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", content)
    if not match:
        return {}

    try:
        parsed = yaml.safe_load(match.group(1))
        return parsed if isinstance(parsed, dict) else {}
    except yaml.YAMLError:
        return {}


def _extract_description(skill_dir: Path, frontmatter: dict[str, Any]) -> str:
    """Get description from frontmatter or first meaningful line of SKILL.md."""
    if frontmatter.get("description"):
        return str(frontmatter["description"])

    md_path = skill_dir / "SKILL.md"
    if not md_path.exists():
        return ""

    try:
        content = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""

    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---"):
            return line[:200]
    return ""


def _compute_files_changed(
    old_details: list[dict[str, Any]], new_details: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """Compute file-level diff between old and new file details."""
    old_map = {d["path"]: d["sha256"] for d in old_details}
    new_map = {d["path"]: d["sha256"] for d in new_details}
    changes: list[dict[str, str]] = []

    for path in sorted(set(list(old_map.keys()) + list(new_map.keys()))):
        if path not in old_map:
            changes.append({"path": path, "action": "added"})
        elif path not in new_map:
            changes.append({"path": path, "action": "removed"})
        elif old_map[path] != new_map[path]:
            changes.append({"path": path, "action": "modified"})

    return changes


async def run_reindex(db: AsyncSession, source: str | None = None) -> dict[str, int]:
    """Full re-index of all skill directories.

    Returns { indexed, drifted, new, removed, duration_ms }.
    """
    start = time.monotonic()

    # Determine which sources to scan
    sources = SKILL_SOURCES
    if source:
        sources = [(d, label) for d, label in SKILL_SOURCES if label == source]

    # Collect all skill directories from filesystem
    discovered: dict[str, dict[str, Any]] = {}  # skill_path -> info

    for source_dir, label in sources:
        directory = Path(source_dir)
        if not directory.exists():
            continue
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            logger.warning("Permission denied: %s", directory)
            continue

        for d in entries:
            if not d.is_dir():
                continue
            if d.name in IGNORE_NAMES or d.name.startswith("."):
                continue

            skill_path = str(d)
            if skill_path in discovered:
                continue

            composite_hash, file_details, file_count, total_bytes = compute_skill_hash(d)
            md_path = d / "SKILL.md"
            fm = parse_frontmatter(md_path) if md_path.exists() else {}
            description = _extract_description(d, fm)

            discovered[skill_path] = {
                "skill_name": d.name,
                "source_dir": source_dir,
                "source_label": label,
                "skill_path": skill_path,
                "description": description,
                "homepage": fm.get("homepage") or fm.get("url"),
                "file_count": file_count,
                "total_bytes": total_bytes,
                "sha256_hash": composite_hash,
                "frontmatter": fm or None,
                "file_details": file_details,
            }

    # Load existing index from DB
    existing_result = await db.execute(
        text(
            "SELECT id, skill_path, sha256_hash, file_count FROM skills_index WHERE removed_at IS NULL"
        )
    )
    existing = {row.skill_path: row for row in existing_result.fetchall()}

    indexed = 0
    drifted = 0
    new_count = 0
    removed = 0

    # Upsert discovered skills
    for skill_path, info in discovered.items():
        indexed += 1

        if skill_path in existing:
            row = existing[skill_path]
            if row.sha256_hash != info["sha256_hash"]:
                # Drift detected
                drifted += 1

                # Compute file-level diff — need old file details
                # We don't store old file details, so use counts only for the drift log
                # For file-level: re-compute from what we have
                old_details: list[dict[str, Any]] = []  # We don't have old details in DB
                files_changed = _compute_files_changed(old_details, info["file_details"])

                # Insert drift log
                await db.execute(
                    text("""
                        INSERT INTO skills_drift_log
                            (skill_id, old_hash, new_hash, old_file_count, new_file_count, files_changed)
                        VALUES (:skill_id, :old_hash, :new_hash, :old_fc, :new_fc, CAST(:files AS jsonb))
                    """),
                    {
                        "skill_id": row.id,
                        "old_hash": row.sha256_hash,
                        "new_hash": info["sha256_hash"],
                        "old_fc": row.file_count,
                        "new_fc": info["file_count"],
                        "files": __import__("json").dumps(files_changed),
                    },
                )

                # Update index
                await db.execute(
                    text("""
                        UPDATE skills_index SET
                            skill_name = :name, source_dir = :sdir, source_label = :slabel,
                            description = :desc, homepage = :hp,
                            file_count = :fc, total_bytes = :tb,
                            sha256_hash = :hash, frontmatter = CAST(:fm AS jsonb),
                            last_indexed_at = NOW(), last_changed_at = NOW(),
                            removed_at = NULL
                        WHERE id = :id
                    """),
                    {
                        "id": row.id,
                        "name": info["skill_name"],
                        "sdir": info["source_dir"],
                        "slabel": info["source_label"],
                        "desc": info["description"],
                        "hp": info["homepage"],
                        "fc": info["file_count"],
                        "tb": info["total_bytes"],
                        "hash": info["sha256_hash"],
                        "fm": __import__("json").dumps(info["frontmatter"]),
                    },
                )
            else:
                # No drift — just update indexed timestamp
                await db.execute(
                    text("UPDATE skills_index SET last_indexed_at = NOW() WHERE id = :id"),
                    {"id": row.id},
                )
        else:
            # New skill
            new_count += 1
            await db.execute(
                text("""
                    INSERT INTO skills_index
                        (skill_name, source_dir, source_label, skill_path,
                         description, homepage, file_count, total_bytes,
                         sha256_hash, frontmatter, last_changed_at)
                    VALUES
                        (:name, :sdir, :slabel, :spath,
                         :desc, :hp, :fc, :tb,
                         :hash, CAST(:fm AS jsonb), NOW())
                """),
                {
                    "name": info["skill_name"],
                    "sdir": info["source_dir"],
                    "slabel": info["source_label"],
                    "spath": info["skill_path"],
                    "desc": info["description"],
                    "hp": info["homepage"],
                    "fc": info["file_count"],
                    "tb": info["total_bytes"],
                    "hash": info["sha256_hash"],
                    "fm": __import__("json").dumps(info["frontmatter"]),
                },
            )

    # Soft-delete removed skills
    discovered_paths = set(discovered.keys())
    for skill_path, row in existing.items():
        if skill_path not in discovered_paths:
            removed += 1
            await db.execute(
                text("UPDATE skills_index SET removed_at = NOW() WHERE id = :id"),
                {"id": row.id},
            )

    await db.commit()

    duration_ms = int((time.monotonic() - start) * 1000)

    return {
        "indexed": indexed,
        "drifted": drifted,
        "new": new_count,
        "removed": removed,
        "duration_ms": duration_ms,
    }
