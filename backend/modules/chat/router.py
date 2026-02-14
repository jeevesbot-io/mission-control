"""Chat module API endpoints."""

from fastapi import APIRouter, HTTPException, Request
from httpx import HTTPStatusError, RequestError, TimeoutException

from core.config import settings
from core.rate_limit import limiter

from .models import ChatHealthResponse, ChatRequest, ChatResponse
from .service import chat_service

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
@limiter.limit("30/minute")
async def send_message(request: Request, body: ChatRequest):
    """Send messages to Jeeves via OpenClaw gateway."""
    try:
        return await chat_service.send_message(body)
    except TimeoutException:
        raise HTTPException(status_code=504, detail="Gateway timeout — LLM took too long to respond")
    except HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Gateway error: {exc.response.status_code}")
    except RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Cannot reach gateway: {exc}")


@router.get("/health", response_model=ChatHealthResponse)
async def chat_health():
    """Check if the OpenClaw gateway is available for chat."""
    available = await chat_service.check_health()
    return ChatHealthResponse(available=available, gateway_url=settings.openclaw_url)
