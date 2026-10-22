from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.init_db import init_db, recover_stale_scans
from app.workers.scan_worker import scan_worker
from app.workers.scheduler import scan_scheduler
from app.utils.logger import logger
from app.utils.event_manager import event_manager
from app.api.targets import router as targets_router
from app.api.scans import router as scans_router
from app.api.results import router as results_router
from app.api.findings import router as findings_router
from app.api.dashboard import router as dashboard_router
from app.api.comparison import router as comparison_router
from app.api.reports import router as reports_router
from app.api.topology import router as topology_router
from app.api.auth import router as auth_router, seed_default_admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database, perform stale scan recovery, seed admin, and start scheduler
    logger.info("Application starting up...")
    init_db()
    recover_stale_scans()
    seed_default_admin()
    scan_scheduler.start()
    yield
    # Shutdown: gracefully shut down scan worker and scheduler
    logger.info("Application shutting down...")
    scan_scheduler.shutdown()
    scan_worker.shutdown(wait=False)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Integrated Network Security Assessment and Reconnaissance Framework",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import correlation_id_ctx, logger

# Request correlation & timing middleware
class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        token = correlation_id_ctx.set(req_id)
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            response.headers["X-Request-ID"] = req_id
            if not request.url.path.startswith("/health") and not request.url.path.startswith("/ws"):
                logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)")
            return response
        finally:
            correlation_id_ctx.reset(token)

app.add_middleware(RequestCorrelationMiddleware)

# Health endpoint
@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

# WebSocket for live scan updates
@app.websocket("/ws/scans")
async def websocket_scans(websocket: WebSocket):
    await event_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_manager.disconnect(websocket)
    except Exception:
        event_manager.disconnect(websocket)

# Include all API routers
app.include_router(targets_router)
app.include_router(scans_router)
app.include_router(results_router)
app.include_router(findings_router)
app.include_router(dashboard_router)
app.include_router(comparison_router)
app.include_router(reports_router)
app.include_router(topology_router)
app.include_router(auth_router)
