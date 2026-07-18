"""Health check router."""

from fastapi import APIRouter

from pros.src.config.settings import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "service": settings.app_name,
    }


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check."""
    health_status = {
        "status": "ok",
        "version": settings.app_version,
        "checks": {}
    }
    
    # Check Ollama
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ai.ollama_base_url}/api/tags")
            if response.status_code == 200:
                health_status["checks"]["ollama"] = "ok"
            else:
                health_status["checks"]["ollama"] = "error"
    except Exception:
        health_status["checks"]["ollama"] = "unavailable"
    
    # Check Redis
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis.url)
        await r.ping()
        await r.close()
        health_status["checks"]["redis"] = "ok"
    except Exception:
        health_status["checks"]["redis"] = "unavailable"
    
    return health_status
