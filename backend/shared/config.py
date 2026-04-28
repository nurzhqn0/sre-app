from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class ServiceSettings:
    service_name: str
    port: int
    database_url: str
    jwt_secret_key: str
    product_service_url: str
    default_chat_room: str


@lru_cache
def get_settings() -> ServiceSettings:
    return ServiceSettings(
        service_name=os.getenv("SERVICE_NAME", "service"),
        port=int(os.getenv("PORT", "8000")),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://sre_user:sre_password@postgres:5432/sre_app",
        ),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
        product_service_url=os.getenv(
            "PRODUCT_SERVICE_URL", "http://product-service:8003"
        ),
        default_chat_room=os.getenv("DEFAULT_CHAT_ROOM", "operations"),
    )
