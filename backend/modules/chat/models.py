"""Pydantic schemas for the Chat module."""

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    session_key: str | None = None


class ChatResponse(BaseModel):
    message: ChatMessage
    usage: dict | None = None


class ChatHealthResponse(BaseModel):
    available: bool
    gateway_url: str
