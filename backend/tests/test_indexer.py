"""Tests for the Skills indexer — hash computation and drift detection."""

import tempfile
from pathlib import Path

from modules.skills.indexer import compute_skill_hash, parse_frontmatter


def test_compute_hash_empty_dir():
    with tempfile.TemporaryDirectory() as d:
        h, details, fc, tb = compute_skill_hash(Path(d))
    assert fc == 0
    assert tb == 0
    assert len(details) == 0


def test_compute_hash_single_file():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "SKILL.md").write_text("# Hello")
        h1, details, fc, tb = compute_skill_hash(p)
    assert fc == 1
    assert tb == 7  # len("# Hello")
    assert len(details) == 1
    assert details[0]["path"] == "SKILL.md"
    # Hash should be deterministic
    with tempfile.TemporaryDirectory() as d2:
        p2 = Path(d2)
        (p2 / "SKILL.md").write_text("# Hello")
        h2, _, _, _ = compute_skill_hash(p2)
    assert h1 == h2


def test_compute_hash_changes_on_content_change():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "SKILL.md").write_text("# Hello")
        h1, _, _, _ = compute_skill_hash(p)
        (p / "SKILL.md").write_text("# Changed")
        h2, _, _, _ = compute_skill_hash(p)
    assert h1 != h2


def test_compute_hash_changes_on_file_add():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "SKILL.md").write_text("# Hello")
        h1, _, fc1, _ = compute_skill_hash(p)
        (p / "extra.md").write_text("extra")
        h2, _, fc2, _ = compute_skill_hash(p)
    assert h1 != h2
    assert fc1 == 1
    assert fc2 == 2


def test_compute_hash_ignores_ds_store():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "SKILL.md").write_text("# Hello")
        h1, _, _, _ = compute_skill_hash(p)
        (p / ".DS_Store").write_text("junk")
        h2, _, _, _ = compute_skill_hash(p)
    assert h1 == h2  # .DS_Store ignored


def test_parse_frontmatter_valid():
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write("---\nname: test\ndescription: A test skill\n---\n# Content")
        f.flush()
        fm = parse_frontmatter(Path(f.name))
    assert fm["name"] == "test"
    assert fm["description"] == "A test skill"


def test_parse_frontmatter_missing():
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write("# No frontmatter")
        f.flush()
        fm = parse_frontmatter(Path(f.name))
    assert fm == {}


def test_parse_frontmatter_nonexistent():
    fm = parse_frontmatter(Path("/nonexistent/SKILL.md"))
    assert fm == {}
