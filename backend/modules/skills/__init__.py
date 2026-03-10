"""Skills Browser module — read-only skill directory scanner."""

from .router import router

MODULE_INFO = {
    "id": "skills",
    "name": "Skills",
    "icon": "🧩",
    "router": router,
    "prefix": "/api/skills",
}
