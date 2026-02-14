"""Chat module service — proxies messages to OpenClaw gateway Chat Completions API."""

import logging

import httpx

from core.config import settings

from .models import ChatMessage, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class ChatService:
    """Proxy chat messages to the OpenClaw gateway."""

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """POST to OpenClaw Chat Completions API and return assistant response."""
        url = f"{settings.openclaw_url}/v1/chat/completions"
        headers: dict[str, str] = {"x-openclaw-agent-id": "main"}

        if settings.openclaw_token:
            headers["Authorization"] = f"Bearer {settings.openclaw_token}"

        if request.session_key:
            headers["x-openclaw-session-key"] = request.session_key

        payload = {
            "model": "main",
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        return ChatResponse(
            message=ChatMessage(role=choice["role"], content=choice["content"]),
            usage=data.get("usage"),
        )

    async def check_health(self) -> bool:
        """Check if the OpenClaw gateway is reachable."""
        url = f"{settings.openclaw_url}/v1/models"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                return resp.status_code < 300
        except httpx.RequestError:
            return False


chat_service = ChatService()
