"""
LinkedIn Job Analyzer — FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_database
from routes import analysis, auth, jobs, resume

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting %s", settings.app_name)
    try:
        init_database()
    except Exception:
        logger.exception("Database initialization failed")
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="AI-powered LinkedIn job matching and analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers (plain paths for local uvicorn, /api for Vercel)
app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(analysis.router)
app.include_router(auth.router, prefix="/api", include_in_schema=False)
app.include_router(resume.router, prefix="/api", include_in_schema=False)
app.include_router(jobs.router, prefix="/api", include_in_schema=False)
app.include_router(analysis.router, prefix="/api", include_in_schema=False)


@app.get("/")
@app.get("/api")
async def root():
    """Health check endpoint."""
    return {
        "app": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "healthy"}
