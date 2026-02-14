"""Chat module — talk to Jeeves via OpenClaw gateway."""

from .router import router

MODULE_INFO = {
    "id": "chat",
    "name": "Chat",
    "icon": "\U0001f4ac",  # 💬
    "router": router,
    "prefix": "/api/chat",
}
