"""Chat module API endpoints."""

from fastapi import APIRouter, HTTPException, Request
from httpx import HTTPStatusError, RequestError, TimeoutException

from core.config import settings
from core.rate_limit import limiter
from modules.activity.models import ActivityLogRequest
from modules.activity.service import activity_service

from .models import ChatHealthResponse, ChatRequest, ChatResponse
from .service import chat_service

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
@limiter.limit("30/minute")
async def send_message(request: Request, body: ChatRequest):
    """Send messages to Jeeves via OpenClaw gateway."""
    try:
        result = await chat_service.send_message(body)
    except TimeoutException:
        raise HTTPException(status_code=504, detail="Gateway timeout — LLM took too long to respond")
    except HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Gateway error: {exc.response.status_code}")
    except RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Cannot reach gateway: {exc}")
    await activity_service.log_event(ActivityLogRequest(
        actor="user", action="chat.sent", resource_type="chat",
        module="chat",
    ))
    return result


@router.get("/health", response_model=ChatHealthResponse)
async def chat_health():
    """Check if the OpenClaw gateway is available for chat."""
    available = await chat_service.check_health()
    return ChatHealthResponse(available=available, gateway_url=settings.openclaw_url)
