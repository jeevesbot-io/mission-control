"""Memory module service — file reading, caching, section parsing, full-text search."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from core.config import settings

from .models import (
    MemoryFileInfo,
    MemorySection,
    SearchHit,
)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _slugify(text: str) -> str:
    """Convert heading text to an anchor-link slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


def _parse_sections(content: str) -> list[MemorySection]:
    """Split markdown content on heading boundaries into sections."""
    sections: list[MemorySection] = []
    matches = list(HEADING_RE.finditer(content))

    for i, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sections.append(
            MemorySection(
                heading=heading,
                slug=_slugify(heading),
                content=body,
                level=level,
            )
        )

    return sections


@dataclass
class CachedFile:
    path: Path
    mtime: float
    content: str
    sections: list[MemorySection] = field(default_factory=list)


class MemoryService:
    """Reads and caches memory markdown files from the filesystem."""

    def __init__(self) -> None:
        self._cache: dict[str, CachedFile] = {}

    @property
    def memory_dir(self) -> Path:
        return settings.memory_dir

    @property
    def long_term_path(self) -> Path:
        return settings.memory_dir.parent / "MEMORY.md"

    def _is_stale(self, filename: str) -> bool:
        """Check if cached entry is stale (file changed or not cached)."""
        cached = self._cache.get(filename)
        if cached is None:
            return True
        try:
            return cached.path.stat().st_mtime != cached.mtime
        except OSError:
            return True

    def _load_file(self, path: Path) -> CachedFile | None:
        """Read a file and parse its sections, returning a CachedFile or None on error."""
        try:
            stat = path.stat()
            content = path.read_text(encoding="utf-8")
        except OSError:
            return None

        sections = _parse_sections(content)
        entry = CachedFile(
            path=path,
            mtime=stat.st_mtime,
            content=content,
            sections=sections,
        )
        self._cache[path.name] = entry
        return entry

    def _get_file(self, filename: str, path: Path) -> CachedFile | None:
        """Get file from cache or load it, returning None if unavailable."""
        if not self._is_stale(filename):
            return self._cache[filename]
        return self._load_file(path)

    def list_daily_files(self) -> list[MemoryFileInfo]:
        """List all daily memory files sorted by date descending."""
        try:
            files = sorted(self.memory_dir.glob("*.md"), reverse=True)
        except OSError:
            return []

        result: list[MemoryFileInfo] = []
        for path in files:
            stem = path.stem
            if not DATE_RE.match(stem):
                continue

            cached = self._get_file(path.name, path)
            if cached is None:
                continue

            # Preview: first non-heading, non-empty line, truncated
            preview = ""
            for line in cached.content.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    preview = stripped[:150]
                    break

            result.append(
                MemoryFileInfo(
                    date=stem,
                    filename=path.name,
                    size=len(cached.content.encode("utf-8")),
                    section_count=len(cached.sections),
                    preview=preview,
                )
            )

        return result

    def get_daily(self, date: str) -> tuple[str, list[MemorySection]] | None:
        """Get content and sections for a daily memory file. Returns None if not found."""
        filename = f"{date}.md"
        path = self.memory_dir / filename
        cached = self._get_file(filename, path)
        if cached is None:
            return None
        return cached.content, cached.sections

    def get_long_term(self) -> tuple[str, list[MemorySection]] | None:
        """Get MEMORY.md content and sections. Returns None if not found."""
        path = self.long_term_path
        cached = self._get_file(path.name, path)
        if cached is None:
            return None
        return cached.content, cached.sections

    def search(self, query: str) -> list[SearchHit]:
        """Case-insensitive full-text search across all memory files."""
        query_lower = query.lower()
        hits: list[SearchHit] = []

        # Search daily files
        try:
            files = sorted(self.memory_dir.glob("*.md"), reverse=True)
        except OSError:
            files = []

        all_files = [(f, f.stem if DATE_RE.match(f.stem) else None) for f in files if f.is_file()]

        # Include MEMORY.md
        lt_path = self.long_term_path
        if lt_path.is_file():
            all_files.append((lt_path, None))

        for path, date in all_files:
            cached = self._get_file(path.name, path)
            if cached is None:
                continue

            current_section: str | None = None
            for line_num, line in enumerate(cached.content.splitlines(), start=1):
                # Track which section we're in
                heading_match = HEADING_RE.match(line)
                if heading_match:
                    current_section = heading_match.group(2).strip()

                if query_lower in line.lower():
                    # Build ~150 char snippet centred on match
                    idx = line.lower().index(query_lower)
                    start = max(0, idx - 60)
                    end = min(len(line), idx + len(query) + 60)
                    snippet = line[start:end].strip()
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(line):
                        snippet = snippet + "..."

                    hits.append(
                        SearchHit(
                            filename=path.name,
                            date=date,
                            line_number=line_num,
                            section_heading=current_section,
                            snippet=snippet,
                        )
                    )

        return hits

    def get_stats(self) -> dict:
        """Lightweight stats for overview widget."""
        try:
            daily_files = [f for f in self.memory_dir.glob("*.md") if DATE_RE.match(f.stem)]
        except OSError:
            daily_files = []

        total_size = 0
        latest_date: str | None = None
        dates: list[str] = []

        for f in daily_files:
            try:
                total_size += f.stat().st_size
                dates.append(f.stem)
            except OSError:
                continue

        if dates:
            dates.sort(reverse=True)
            latest_date = dates[0]

        # Include MEMORY.md size
        try:
            total_size += self.long_term_path.stat().st_size
        except OSError:
            pass

        return {
            "total_files": len(daily_files),
            "latest_date": latest_date,
            "total_size_bytes": total_size,
            "has_long_term": self.long_term_path.is_file(),
        }


# Module-level singleton
memory_service = MemoryService()
