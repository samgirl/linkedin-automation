import sys
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.api import auth, connectors, context, opportunities, drafts, journal, dashboard, scanner

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PROS API",
    description="Personal Reputation Operating System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimiterMiddleware, requests_per_minute=120)

app.include_router(auth.router)
app.include_router(connectors.router)
app.include_router(context.router)
app.include_router(opportunities.router)
app.include_router(drafts.router)
app.include_router(journal.router)
app.include_router(dashboard.router)
app.include_router(scanner.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
