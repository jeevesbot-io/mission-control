"""Content module business logic."""

import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import Optional
from uuid import uuid4

from core.config import settings

from .models import (
    ContentCreate,
    ContentItem,
    ContentPipelineResponse,
    ContentUpdate,
)

logger = logging.getLogger(__name__)

_lock = threading.Lock()


class ContentService:
    """Service for content pipeline operations."""

    def __init__(self):
        """Initialize content service."""
        self.content_file = settings.dashboard_data_path / "content.json"
        self._ensure_file()

    def _ensure_file(self):
        """Ensure content file exists."""
        if not self.content_file.exists():
            self.content_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_data_sync({"items": []})

    def _read_data_sync(self) -> dict:
        """Read content data from file (sync, call via to_thread)."""
        with _lock:
            try:
                with open(self.content_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Error reading content data: %s", e)
                return {"items": []}

    def _write_data_sync(self, data: dict):
        """Write content data to file (sync, call via to_thread)."""
        with _lock:
            try:
                with open(self.content_file, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.warning("Error writing content data: %s", e)

    async def get_pipeline(self) -> ContentPipelineResponse:
        """Get all content items grouped by stage."""
        data = await asyncio.to_thread(self._read_data_sync)
        items = [ContentItem(**item) for item in data.get("items", [])]

        # Calculate stats
        stats = {
            "total": len(items),
            "by_stage": {},
            "by_type": {},
        }

        for item in items:
            # Stage counts
            stage = item.stage
            stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1

            # Type counts
            item_type = item.type
            stats["by_type"][item_type] = stats["by_type"].get(item_type, 0) + 1

        return ContentPipelineResponse(items=items, stats=stats)

    async def create_item(self, create: ContentCreate) -> ContentItem:
        """Create a new content item."""
        def _create():
            data = self._read_data_sync()
            now = datetime.utcnow()
            item = ContentItem(
                id=str(uuid4()),
                title=create.title,
                description=create.description,
                type=create.type,
                stage=create.stage,
                tags=create.tags,
                priority=create.priority,
                created_at=now,
                updated_at=now,
            )
            data["items"].append(item.model_dump(mode="json"))
            self._write_data_sync(data)
            return item

        return await asyncio.to_thread(_create)

    async def update_item(self, item_id: str, update: ContentUpdate) -> Optional[ContentItem]:
        """Update a content item."""
        def _update():
            data = self._read_data_sync()
            items = data.get("items", [])

            for i, item in enumerate(items):
                if item["id"] == item_id:
                    if update.title is not None:
                        item["title"] = update.title
                    if update.description is not None:
                        item["description"] = update.description
                    if update.stage is not None:
                        item["stage"] = update.stage
                    if update.script is not None:
                        item["script"] = update.script
                    if update.thumbnail_url is not None:
                        item["thumbnail_url"] = update.thumbnail_url
                    if update.video_url is not None:
                        item["video_url"] = update.video_url
                    if update.published_url is not None:
                        item["published_url"] = update.published_url
                    if update.tags is not None:
                        item["tags"] = update.tags
                    if update.assigned_to is not None:
                        item["assigned_to"] = update.assigned_to
                    if update.priority is not None:
                        item["priority"] = update.priority

                    item["updated_at"] = datetime.utcnow().isoformat()
                    data["items"][i] = item
                    self._write_data_sync(data)
                    return ContentItem(**item)

            return None

        return await asyncio.to_thread(_update)

    async def delete_item(self, item_id: str) -> bool:
        """Delete a content item."""
        def _delete():
            data = self._read_data_sync()
            items = data.get("items", [])
            filtered = [item for item in items if item["id"] != item_id]
            if len(filtered) < len(items):
                data["items"] = filtered
                self._write_data_sync(data)
                return True
            return False

        return await asyncio.to_thread(_delete)

    async def move_item(
        self,
        item_id: str,
        target_stage: str,
    ) -> Optional[ContentItem]:
        """Move item to a different stage."""
        update = ContentUpdate(stage=target_stage)  # type: ignore
        return await self.update_item(item_id, update)


content_service = ContentService()
