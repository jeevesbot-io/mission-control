"""School module — events, emails, and tasks dashboard."""

from .router import router

MODULE_INFO = {
    "id": "school",
    "name": "School",
    "icon": "\U0001f393",  # 🎓
    "router": router,
    "prefix": "/api/school",
}
