"""Office module — visual agent workspace and activity monitor."""

from .router import router

MODULE_INFO = {
    "id": "office",
    "name": "Office View",
    "icon": "🏢",
    "router": router,
    "prefix": "/api/office",
}
