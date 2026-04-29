from __future__ import annotations

import time
from typing import Callable

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


REQUEST_COUNTER = Counter(
    "service_http_requests_total",
    "Total HTTP requests handled by the service.",
    ["service", "method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "service_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["service", "method", "path"],
)

SERVICE_HEALTH_STATUS = Gauge(
    "service_health_status",
    "Logical health state for a service. 1 means healthy, 0 means unhealthy.",
    ["service"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        path = request.url.path

        REQUEST_COUNTER.labels(
            service=self.service_name,
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()
        REQUEST_LATENCY.labels(
            service=self.service_name,
            method=request.method,
            path=path,
        ).observe(duration)
        return response


def metrics_response(
    service_name: str,
    health_check: Callable[[], None] | None = None,
) -> Response:
    if health_check is not None:
        try:
            health_check()
            SERVICE_HEALTH_STATUS.labels(service=service_name).set(1)
        except Exception:
            SERVICE_HEALTH_STATUS.labels(service=service_name).set(0)
    else:
        SERVICE_HEALTH_STATUS.labels(service=service_name).set(1)

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
