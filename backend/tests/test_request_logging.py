"""Tests for request logging middleware."""

import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from core.request_logging import RequestLoggingMiddleware


def _create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/api/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/api/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def app():
    return _create_test_app()


@pytest.fixture
def transport(app):
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_logging_happy_path(transport, caplog):
    """Normal request should produce a structured log entry."""
    with caplog.at_level(logging.INFO, logger="core.request_logging"):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/test")
    assert resp.status_code == 200

    log_records = [r for r in caplog.records if r.message == "request completed"]
    assert len(log_records) == 1
    rec = log_records[0]
    assert rec.method == "GET"
    assert rec.path == "/api/test"
    assert rec.status_code == 200
    assert rec.duration_ms >= 0


@pytest.mark.asyncio
async def test_logging_skips_health(transport, caplog):
    """/api/health should NOT be logged."""
    with caplog.at_level(logging.INFO, logger="core.request_logging"):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/api/health")

    log_records = [r for r in caplog.records if r.message == "request completed"]
    assert len(log_records) == 0


@pytest.mark.asyncio
async def test_logging_duration_positive(transport, caplog):
    """duration_ms should be a positive number."""
    with caplog.at_level(logging.INFO, logger="core.request_logging"):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/api/test")

    log_records = [r for r in caplog.records if r.message == "request completed"]
    assert len(log_records) == 1
    assert log_records[0].duration_ms > 0
