from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.init_db import init_db, recover_stale_scans
from app.workers.scan_worker import scan_worker
from app.utils.logger import logger
from app.api.targets import router as targets_router
from app.api.scans import router as scans_router
from app.api.results import router as results_router
from app.api.findings import router as findings_router
from app.api.dashboard import router as dashboard_router
from app.api.comparison import router as comparison_router
from app.api.reports import router as reports_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and perform stale scan recovery
    logger.info("Application starting up...")
    init_db()
    recover_stale_scans()
    yield
    # Shutdown: gracefully shut down scan worker
    logger.info("Application shutting down...")
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

# Health endpoint
@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

# Include all API routers
app.include_router(targets_router)
app.include_router(scans_router)
app.include_router(results_router)
app.include_router(findings_router)
app.include_router(dashboard_router)
app.include_router(comparison_router)
app.include_router(reports_router)
