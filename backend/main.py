import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from core.cloudflare_auth import CloudflareAccessMiddleware, validate_cf_token
from core.config import settings
from core.database import async_session, engine
from core.logging_config import setup_logging
from core.models import HealthResponse, ModuleInfoResponse
from core.rate_limit import limiter
from core.registry import discover_modules
from core.security_headers import SecurityHeadersMiddleware
from core.websocket import manager

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Mission Control starting up")
    yield
    await engine.dispose()
    logger.info("Mission Control shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Mission Control", version="0.1.0", lifespan=lifespan)

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Middleware stack (outermost first)
    # 1. Security headers (outermost — runs on every response)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Cloudflare Access auth (skipped when cf_access_team is empty)
    app.add_middleware(CloudflareAccessMiddleware)

    # 3. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Cf-Access-Jwt-Assertion"],
    )

    # Discover and mount modules
    modules = discover_modules()
    for mod in modules:
        app.include_router(mod["router"], prefix=mod["prefix"], tags=[mod["name"]])
        logger.info("Mounted module: %s at %s", mod["name"], mod["prefix"])

    # Store module info for /api/modules endpoint
    app.state.modules = modules

    # Core routes
    @app.get("/api/health", response_model=HealthResponse)
    async def health_check():
        db_ok = True
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
        except Exception:
            db_ok = False
            logger.warning("Health check: database unreachable")
        return HealthResponse(
            status="ok" if db_ok else "degraded",
            database=db_ok,
        )

    @app.get("/api/modules", response_model=list[ModuleInfoResponse])
    async def list_modules():
        return [
            ModuleInfoResponse(
                id=m["id"], name=m["name"], icon=m["icon"], prefix=m["prefix"]
            )
            for m in app.state.modules
        ]

    # WebSocket
    @app.websocket("/ws/live")
    async def websocket_endpoint(websocket: WebSocket):
        # Validate CF Access token on WebSocket when enabled
        if settings.cf_access_team:
            token = websocket.cookies.get("CF_Authorization")
            if not token:
                await websocket.close(code=4003, reason="Missing CF Access token")
                return
            email = await validate_cf_token(token)
            if not email:
                await websocket.close(code=4003, reason="Invalid CF Access token")
                return

        await manager.connect(websocket)
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                action = msg.get("action")
                topic = msg.get("topic")
                if action == "subscribe" and topic:
                    manager.subscribe(websocket, topic)
                elif action == "unsubscribe" and topic:
                    manager.unsubscribe(websocket, topic)
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    # Serve built frontend in production (static/ dir from Vite build)
    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve Vue SPA — all non-API routes fall through to index.html."""
            file = static_dir / full_path
            if file.is_file():
                return FileResponse(file)
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()
