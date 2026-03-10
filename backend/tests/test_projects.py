"""Integration tests for the Projects module."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_modules_includes_projects():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "projects" in ids


def test_list_projects():
    """Should return projects with task/agent counts."""
    from modules.projects.models import ProjectWithCounts

    projects = [
        ProjectWithCounts(
            id="mc",
            name="Mission Control",
            icon="🚀",
            color="#3b82f6",
            status="active",
            task_count=5,
            agent_count=2,
        ),
        ProjectWithCounts(
            id="content",
            name="Content Pipeline",
            icon="📝",
            color="#22c55e",
            status="active",
            task_count=3,
            agent_count=1,
        ),
    ]
    with patch("modules.projects.service.list_projects", new_callable=AsyncMock) as mock:
        mock.return_value = projects
        response = client.get("/api/projects/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "mc"
        assert data[0]["task_count"] == 5
        assert data[1]["name"] == "Content Pipeline"


def test_list_projects_empty():
    """Should handle no projects."""
    with patch("modules.projects.service.list_projects", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = client.get("/api/projects/")
        assert response.status_code == 200
        assert response.json() == []


def test_create_project():
    """Should create a project and return 201."""
    from modules.projects.models import ProjectWithCounts

    created = ProjectWithCounts(
        id="new-proj",
        name="New Project",
        icon="📂",
        color="",
        status="active",
        task_count=0,
        agent_count=0,
    )
    with patch("modules.projects.service.create_project", new_callable=AsyncMock) as mock:
        mock.return_value = created
        response = client.post(
            "/api/projects/",
            json={"id": "new-proj", "name": "New Project"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "new-proj"
        assert data["name"] == "New Project"
        assert data["task_count"] == 0


def test_create_project_missing_fields():
    """Should return 422 when required fields are missing."""
    response = client.post("/api/projects/", json={})
    assert response.status_code == 422


def test_create_project_duplicate():
    """Should return 422 on duplicate project ID."""
    with patch("modules.projects.service.create_project", new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("duplicate key value violates unique constraint")
        response = client.post(
            "/api/projects/",
            json={"id": "existing", "name": "Existing"},
        )
        assert response.status_code == 422
        assert "already exists" in response.json()["detail"]


def test_update_project():
    """Should update a project and return the updated version."""
    from modules.projects.models import ProjectWithCounts

    updated = ProjectWithCounts(
        id="mc",
        name="Mission Control v2",
        icon="🚀",
        color="#3b82f6",
        status="active",
        task_count=5,
        agent_count=2,
    )
    with patch("modules.projects.service.update_project", new_callable=AsyncMock) as mock:
        mock.return_value = updated
        response = client.patch(
            "/api/projects/mc",
            json={"name": "Mission Control v2"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Mission Control v2"


def test_update_project_not_found():
    """Should return 404 when project does not exist."""
    with patch("modules.projects.service.update_project", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.patch(
            "/api/projects/nonexistent",
            json={"name": "Updated"},
        )
        assert response.status_code == 404


def test_delete_project():
    """Should delete a project and return ok."""
    with patch("modules.projects.service.delete_project", new_callable=AsyncMock) as mock:
        mock.return_value = (True, None)
        response = client.delete("/api/projects/mc")
        assert response.status_code == 200
        assert response.json()["ok"] is True


def test_delete_project_not_found():
    """Should return 404 when project does not exist."""
    with patch("modules.projects.service.delete_project", new_callable=AsyncMock) as mock:
        mock.return_value = (False, "Project not found")
        response = client.delete("/api/projects/nonexistent")
        assert response.status_code == 404


def test_delete_project_has_tasks():
    """Should return 422 when project has tasks."""
    with patch("modules.projects.service.delete_project", new_callable=AsyncMock) as mock:
        mock.return_value = (
            False,
            "Cannot delete project with existing tasks. Reassign or delete tasks first.",
        )
        response = client.delete("/api/projects/mc")
        assert response.status_code == 422
        assert "Cannot delete" in response.json()["detail"]


def test_get_project_detail():
    """Should return project detail with tasks and agents."""
    from modules.projects.models import ProjectDetail, TaskSummary

    detail = ProjectDetail(
        id="mc",
        name="Mission Control",
        icon="🚀",
        color="#3b82f6",
        status="active",
        task_count=1,
        agent_count=1,
        tasks=[
            TaskSummary(
                id=1,
                title="Build dashboard",
                state="in_progress",
                priority=2,
                agent_id="main",
                tags=["frontend"],
            )
        ],
        agent_ids=["main"],
    )
    with patch("modules.projects.service.get_project", new_callable=AsyncMock) as mock:
        mock.return_value = detail
        response = client.get("/api/projects/mc")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "mc"
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "Build dashboard"
        assert data["agent_ids"] == ["main"]


def test_get_project_not_found():
    """Should return 404 when project does not exist."""
    with patch("modules.projects.service.get_project", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = client.get("/api/projects/nonexistent")
        assert response.status_code == 404
