"""Calendar module — cron jobs, scheduled tasks, and timeline view."""

from .router import router

MODULE_INFO = {
    "id": "calendar",
    "name": "Calendar",
    "icon": "📅",
    "router": router,
    "prefix": "/api/calendar",
}
