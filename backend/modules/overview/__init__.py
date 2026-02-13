"""Overview module — system dashboard and summary data."""

from .router import router

MODULE_INFO = {
    "id": "overview",
    "name": "Overview",
    "icon": "\U0001f3e0",  # 🏠
    "router": router,
    "prefix": "/api/overview",
}
