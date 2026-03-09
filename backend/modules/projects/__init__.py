"""Projects module — first-class project management."""

from .router import router

MODULE_INFO = {
    "id": "projects",
    "name": "Projects",
    "icon": "📂",
    "router": router,
    "prefix": "/api/projects",
}
