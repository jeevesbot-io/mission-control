import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.database import engine
from core.models import HealthResponse, ModuleInfoResponse
from core.registry import discover_modules
from core.websocket import manager

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Mission Control starting up")
    yield
    await engine.dispose()
    logger.info("Mission Control shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Mission Control", version="0.1.0", lifespan=lifespan)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
        return HealthResponse()

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
