"""Skills browser service — scans skill directories for metadata."""

import re
from pathlib import Path


SKILL_DIRS = [
    ("managed", Path("~/.openclaw/skills/").expanduser()),
    ("workspace", Path("~/.openclaw/workspace/skills/").expanduser()),
    ("agent", Path("~/.agents/skills/").expanduser()),
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
                    }
                )

        return skills

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


skills_browser_service = SkillsBrowserService()
