"""Content module — content pipeline for ideas to published content."""

from .router import router

MODULE_INFO = {
    "id": "content",
    "name": "Content Pipeline",
    "icon": "🎬",
    "router": router,
    "prefix": "/api/content",
}
