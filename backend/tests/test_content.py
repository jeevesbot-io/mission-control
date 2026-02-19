"""Integration tests for the Content Pipeline module."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_content():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "content" in ids


def test_get_pipeline_empty():
    from modules.content.models import ContentPipelineResponse

    with patch("modules.content.service.ContentService.get_pipeline", new_callable=AsyncMock) as mock:
        mock.return_value = ContentPipelineResponse(items=[], stats={"total": 0, "by_stage": {}, "by_type": {}})
        response = client.get("/api/content/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["stats"]["total"] == 0


def test_get_pipeline_with_items():
    from modules.content.models import ContentItem, ContentPipelineResponse
    from datetime import datetime

    items = [
        ContentItem(
            id="item-1", title="My Video", stage="ideas", type="video",
            priority="high", created_at=datetime(2026, 2, 18), updated_at=datetime(2026, 2, 18),
        ),
        ContentItem(
            id="item-2", title="Blog Post", stage="scripting", type="article",
            priority="medium", created_at=datetime(2026, 2, 18), updated_at=datetime(2026, 2, 18),
        ),
    ]
    stats = {"total": 2, "by_stage": {"ideas": 1, "scripting": 1}, "by_type": {"video": 1, "article": 1}}
    with patch("modules.content.service.ContentService.get_pipeline", new_callable=AsyncMock) as mock:
        mock.return_value = ContentPipelineResponse(items=items, stats=stats)
        response = client.get("/api/content/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["stats"]["total"] == 2


def test_create_content_item():
    from modules.content.models import ContentItem
    from datetime import datetime

    created = ContentItem(
        id="new-1", title="New Content", stage="ideas", type="video",
        priority="medium", created_at=datetime(2026, 2, 18), updated_at=datetime(2026, 2, 18),
    )
    with patch("modules.content.service.ContentService.create_item", new_callable=AsyncMock) as mock:
        mock.return_value = created
        response = client.post("/api/content/", json={"title": "New Content"})
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "new-1"
        assert data["title"] == "New Content"
        assert data["stage"] == "ideas"


def test_update_content_item():
    from modules.content.models import ContentItem
    from datetime import datetime

    updated = ContentItem(
        id="item-1", title="Updated Title", stage="scripting", type="video",
        priority="high", created_at=datetime(2026, 2, 18), updated_at=datetime(2026, 2, 19),
    )
    with patch("modules.content.service.ContentService.update_item", new_callable=AsyncMock) as mock:
        mock.return_value = updated
        response = client.patch("/api/content/item-1", json={"title": "Updated Title"})
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"


def test_update_content_item_not_found():
    with patch("modules.content.service.ContentService.update_item", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.patch("/api/content/nope", json={"title": "x"})
        assert response.status_code == 404


def test_delete_content_item():
    with patch("modules.content.service.ContentService.delete_item", new_callable=AsyncMock) as mock:
        mock.return_value = True
        response = client.delete("/api/content/item-1")
        assert response.status_code == 204


def test_delete_content_item_not_found():
    with patch("modules.content.service.ContentService.delete_item", new_callable=AsyncMock) as mock:
        mock.return_value = False
        response = client.delete("/api/content/nope")
        assert response.status_code == 404


def test_move_content_item():
    from modules.content.models import ContentItem
    from datetime import datetime

    moved = ContentItem(
        id="item-1", title="My Video", stage="editing", type="video",
        priority="medium", created_at=datetime(2026, 2, 18), updated_at=datetime(2026, 2, 19),
    )
    with patch("modules.content.service.ContentService.move_item", new_callable=AsyncMock) as mock:
        mock.return_value = moved
        response = client.post("/api/content/item-1/move/editing")
        assert response.status_code == 200
        assert response.json()["stage"] == "editing"


def test_move_content_item_not_found():
    with patch("modules.content.service.ContentService.move_item", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.post("/api/content/nope/move/editing")
        assert response.status_code == 404
