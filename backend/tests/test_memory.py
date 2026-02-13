"""Integration tests for the Memory module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# Sample markdown content for testing
SAMPLE_DAILY = """\
# 2026-01-15

## Morning Standup

- Reviewed pull requests
- Discussed deployment plan

## Afternoon Tasks

- Fixed bug in auth module
- Wrote unit tests for search feature
"""

SAMPLE_MEMORY_MD = """\
# Long-Term Memory

## Key People

- Alice: engineering lead
- Bob: product manager

## Project Notes

Important decisions and context.
"""


def _setup_temp_memory(tmp_path: Path):
    """Create temp memory dir with sample files."""
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()

    (memory_dir / "2026-01-15.md").write_text(SAMPLE_DAILY)
    (memory_dir / "2026-01-14.md").write_text("# 2026-01-14\n\n## Short Day\n\nNot much.\n")

    # MEMORY.md lives in the parent of memory_dir
    (tmp_path / "MEMORY.md").write_text(SAMPLE_MEMORY_MD)

    return memory_dir


class TestMemoryFiles:
    def test_list_files(self, tmp_path):
        memory_dir = _setup_temp_memory(tmp_path)
        with patch("modules.memory.service.settings") as mock_settings:
            mock_settings.memory_dir = memory_dir
            # Re-init the service cache
            from modules.memory.service import memory_service

            memory_service._cache.clear()

            response = client.get("/api/memory/files")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            # Files should be sorted newest first
            assert data["files"][0]["date"] == "2026-01-15"
            assert data["files"][1]["date"] == "2026-01-14"
            assert data["files"][0]["section_count"] > 0
            assert len(data["files"][0]["preview"]) > 0

    def test_get_daily_valid(self, tmp_path):
        memory_dir = _setup_temp_memory(tmp_path)
        with patch("modules.memory.service.settings") as mock_settings:
            mock_settings.memory_dir = memory_dir
            from modules.memory.service import memory_service

            memory_service._cache.clear()

            response = client.get("/api/memory/files/2026-01-15")
            assert response.status_code == 200
            data = response.json()
            assert data["date"] == "2026-01-15"
            assert "Morning Standup" in data["content"]
            assert len(data["sections"]) >= 2
            slugs = [s["slug"] for s in data["sections"]]
            assert "morning-standup" in slugs

    def test_get_daily_missing(self, tmp_path):
        memory_dir = _setup_temp_memory(tmp_path)
        with patch("modules.memory.service.settings") as mock_settings:
            mock_settings.memory_dir = memory_dir
            from modules.memory.service import memory_service

            memory_service._cache.clear()

            response = client.get("/api/memory/files/1999-01-01")
            assert response.status_code == 404

    def test_get_daily_invalid_format(self, tmp_path):
        memory_dir = _setup_temp_memory(tmp_path)
        with patch("modules.memory.service.settings") as mock_settings:
            mock_settings.memory_dir = memory_dir
            from modules.memory.service import memory_service

            memory_service._cache.clear()

            response = client.get("/api/memory/files/not-a-date")
            assert response.status_code == 404


class TestLongTermMemory:
    def test_get_long_term(self, tmp_path):
        memory_dir = _setup_temp_memory(tmp_path)
        with patch("modules.memory.service.settings") as mock_settings:
            mock_settings.memory_dir = memory_dir
            from modules.memory.service import memory_service

            memory_service._cache.clear()

            response = client.get("/api/memory/long-term")
            assert response.status_code == 200
            data = response.json()
            assert "Key People" in data["content"]
            assert len(data["sections"]) >= 2


class TestSearch:
    def test_search_with_results(self, tmp_path):
        memory_dir = _setup_temp_memory(tmp_path)
        with patch("modules.memory.service.settings") as mock_settings:
            mock_settings.memory_dir = memory_dir
            from modules.memory.service import memory_service

            memory_service._cache.clear()

            response = client.get("/api/memory/search", params={"q": "auth"})
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "auth"
            assert data["total"] > 0
            assert any("auth" in h["snippet"].lower() for h in data["hits"])

    def test_search_no_results(self, tmp_path):
        memory_dir = _setup_temp_memory(tmp_path)
        with patch("modules.memory.service.settings") as mock_settings:
            mock_settings.memory_dir = memory_dir
            from modules.memory.service import memory_service

            memory_service._cache.clear()

            response = client.get("/api/memory/search", params={"q": "xyznonexistent"})
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["hits"] == []

    def test_search_too_short(self):
        response = client.get("/api/memory/search", params={"q": "a"})
        assert response.status_code == 422  # Validation error


class TestStats:
    def test_stats(self, tmp_path):
        memory_dir = _setup_temp_memory(tmp_path)
        with patch("modules.memory.service.settings") as mock_settings:
            mock_settings.memory_dir = memory_dir
            from modules.memory.service import memory_service

            memory_service._cache.clear()

            response = client.get("/api/memory/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["total_files"] == 2
            assert data["latest_date"] == "2026-01-15"
            assert data["total_size_bytes"] > 0
            assert data["has_long_term"] is True
