from __future__ import annotations
import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

MAX_REQUESTS = 30
WINDOW_SECONDS = 60


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._windows: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/query" and request.method == "POST":
            ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            window = self._windows[ip]

            while window and window[0] < now - WINDOW_SECONDS:
                window.popleft()

            if len(window) >= MAX_REQUESTS:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {MAX_REQUESTS} requests per {WINDOW_SECONDS}s."
                )

            window.append(now)

        return await call_next(request)
