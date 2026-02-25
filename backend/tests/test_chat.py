"""Integration tests for the Chat module."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from httpx import ConnectError, HTTPStatusError, Request, Response, TimeoutException

from main import app

client = TestClient(app)


def test_modules_includes_chat():
    response = client.get("/api/modules")
    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert "chat" in ids


def test_send_message_success():
    """Should proxy message to gateway and return response."""
    from modules.chat.models import ChatMessage, ChatResponse

    mock_response = ChatResponse(
        message=ChatMessage(role="assistant", content="Hello! How can I help?"),
        usage={"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    )
    with patch(
        "modules.chat.service.ChatService.send_message", new_callable=AsyncMock
    ) as mock:
        mock.return_value = mock_response
        response = client.post(
            "/api/chat/send",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"]["role"] == "assistant"
        assert data["message"]["content"] == "Hello! How can I help?"
        assert data["usage"]["total_tokens"] == 18


def test_send_message_gateway_timeout():
    """Should return 504 when gateway times out."""
    with patch(
        "modules.chat.service.ChatService.send_message", new_callable=AsyncMock
    ) as mock:
        mock.side_effect = TimeoutException("timed out")
        response = client.post(
            "/api/chat/send",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 504


def test_send_message_gateway_unreachable():
    """Should return 502 when gateway is unreachable."""
    with patch(
        "modules.chat.service.ChatService.send_message", new_callable=AsyncMock
    ) as mock:
        mock.side_effect = ConnectError("connection refused")
        response = client.post(
            "/api/chat/send",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 502


def test_send_message_gateway_http_error():
    """Should return 502 when gateway returns HTTP error."""
    with patch(
        "modules.chat.service.ChatService.send_message", new_callable=AsyncMock
    ) as mock:
        mock_request = Request("POST", "http://test")
        mock_resp = Response(500, request=mock_request)
        mock.side_effect = HTTPStatusError("server error", request=mock_request, response=mock_resp)
        response = client.post(
            "/api/chat/send",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert response.status_code == 502


def test_send_message_empty_messages():
    """Should handle empty messages list."""
    from modules.chat.models import ChatMessage, ChatResponse

    mock_response = ChatResponse(
        message=ChatMessage(role="assistant", content="How can I help?"),
        usage=None,
    )
    with patch(
        "modules.chat.service.ChatService.send_message", new_callable=AsyncMock
    ) as mock:
        mock.return_value = mock_response
        response = client.post("/api/chat/send", json={"messages": []})
        assert response.status_code == 200


def test_chat_health_available():
    """Should report gateway as available."""
    with patch(
        "modules.chat.service.ChatService.check_health", new_callable=AsyncMock
    ) as mock:
        mock.return_value = True
        response = client.get("/api/chat/health")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert "gateway_url" in data


def test_chat_health_unavailable():
    """Should report gateway as unavailable."""
    with patch(
        "modules.chat.service.ChatService.check_health", new_callable=AsyncMock
    ) as mock:
        mock.return_value = False
        response = client.get("/api/chat/health")
        assert response.status_code == 200
        assert response.json()["available"] is False


def test_chat_health_response_includes_gateway_url():
    """Health response must include a non-empty gateway_url field."""
    with patch(
        "modules.chat.service.ChatService.check_health", new_callable=AsyncMock
    ) as mock:
        mock.return_value = True
        response = client.get("/api/chat/health")
        assert response.status_code == 200
        data = response.json()
        assert "gateway_url" in data
        assert isinstance(data["gateway_url"], str)
        assert len(data["gateway_url"]) > 0


def test_send_message_missing_messages_field_returns_422():
    """Should return 422 when the required 'messages' field is absent."""
    response = client.post("/api/chat/send", json={})
    assert response.status_code == 422


def test_send_message_invalid_message_type_returns_422():
    """Should return 422 when a message entry is not an object."""
    response = client.post("/api/chat/send", json={"messages": ["not-an-object"]})
    assert response.status_code == 422


def test_send_message_with_session_key():
    """Should accept an optional session_key and pass it through to the service."""
    from modules.chat.models import ChatMessage, ChatResponse

    mock_response = ChatResponse(
        message=ChatMessage(role="assistant", content="Got it"),
        usage=None,
    )
    with patch(
        "modules.chat.service.ChatService.send_message", new_callable=AsyncMock
    ) as mock:
        mock.return_value = mock_response
        response = client.post(
            "/api/chat/send",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "session_key": "session-abc-123",
            },
        )
        assert response.status_code == 200
        # Verify session_key was forwarded to the service
        received_request = mock.call_args[0][0]
        assert received_request.session_key == "session-abc-123"


def test_send_message_response_schema():
    """Response must include message.role and message.content fields."""
    from modules.chat.models import ChatMessage, ChatResponse

    mock_response = ChatResponse(
        message=ChatMessage(role="assistant", content="Schema check"),
        usage={"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    )
    with patch(
        "modules.chat.service.ChatService.send_message", new_callable=AsyncMock
    ) as mock:
        mock.return_value = mock_response
        response = client.post(
            "/api/chat/send",
            json={"messages": [{"role": "user", "content": "Check schema"}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"]["role"] == "assistant"
        assert data["message"]["content"] == "Schema check"
        assert data["usage"]["total_tokens"] == 8
