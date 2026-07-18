"""FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pros.src.config.settings import settings
from pros.src.db.database import init_db, close_db
from pros.src.api.routers import (
    events, memory, identity, ai, health,
    content, briefing, workers,
    opportunity, reflection,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Personal Reputation Operating System - AI Coworker",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
    app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
    app.include_router(identity.router, prefix="/api/v1/identity", tags=["identity"])
    app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
    app.include_router(reflection.router, prefix="/api/v1/reflection", tags=["reflection"])
    app.include_router(opportunity.router, prefix="/api/v1/opportunity", tags=["opportunity"])
    app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
    app.include_router(briefing.router, prefix="/api/v1/briefing", tags=["briefing"])
    app.include_router(workers.router, prefix="/api/v1/workers", tags=["workers"])
    
    return app
