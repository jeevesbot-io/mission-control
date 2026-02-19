"""Activity Timeline module — cross-module event feed."""

from .router import router

MODULE_INFO = {
    "id": "activity",
    "name": "Activity Timeline",
    "icon": "📡",
    "router": router,
    "prefix": "/api/activity",
}
