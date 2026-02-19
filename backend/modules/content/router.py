"""Content module API endpoints."""

from fastapi import APIRouter, HTTPException

from .models import (
    ContentCreate,
    ContentItem,
    ContentPipelineResponse,
    ContentUpdate,
)
from modules.activity.models import ActivityLogRequest
from modules.activity.service import activity_service

from .service import content_service

router = APIRouter()


@router.get("/", response_model=ContentPipelineResponse)
async def get_pipeline():
    """Get the full content pipeline."""
    return await content_service.get_pipeline()


@router.post("/", response_model=ContentItem, status_code=201)
async def create_content(create: ContentCreate):
    """Create a new content item."""
    item = await content_service.create_item(create)
    await activity_service.log_event(ActivityLogRequest(
        actor="user", action="content.created", resource_type="content",
        resource_id=item.id, resource_name=item.title, module="content",
    ))
    return item


@router.patch("/{item_id}", response_model=ContentItem)
async def update_content(item_id: str, update: ContentUpdate):
    """Update a content item."""
    item = await content_service.update_item(item_id, update)
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    await activity_service.log_event(ActivityLogRequest(
        actor="user", action="content.updated", resource_type="content",
        resource_id=item.id, resource_name=item.title, module="content",
    ))
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_content(item_id: str):
    """Delete a content item."""
    success = await content_service.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Content item not found")
    await activity_service.log_event(ActivityLogRequest(
        actor="user", action="content.deleted", resource_type="content",
        resource_id=item_id, module="content",
    ))


@router.post("/{item_id}/move/{target_stage}", response_model=ContentItem)
async def move_content(item_id: str, target_stage: str):
    """Move content item to a different stage."""
    item = await content_service.move_item(item_id, target_stage)
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    await activity_service.log_event(ActivityLogRequest(
        actor="user", action="content.moved", resource_type="content",
        resource_id=item.id, resource_name=item.title, module="content",
        details={"target_stage": target_stage},
    ))
    return item
