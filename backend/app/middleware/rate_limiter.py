import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = {}
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
            )

        self.requests[client_ip].append(now)

        if now - self._last_cleanup > 300:
            self._last_cleanup = now
            stale = [ip for ip, times in self.requests.items() if not times or now - times[-1] > 300]
            for ip in stale:
                del self.requests[ip]

        response = await call_next(request)
        return response
