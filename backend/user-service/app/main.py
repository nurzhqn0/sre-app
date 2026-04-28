from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status

from shared.auth import require_user_claims
from shared.config import get_settings
from shared.database import check_database, get_connection
from shared.metrics import MetricsMiddleware, metrics_response

settings = get_settings()
app = FastAPI(title="User Service", version="1.0.0")
app.add_middleware(MetricsMiddleware, service_name=settings.service_name)


def current_user(authorization: Annotated[str | None, Header()] = None):
    return require_user_claims(settings.jwt_secret_key, authorization)


@app.get("/health")
def health():
    check_database(settings.database_url)
    return {"service": settings.service_name, "status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.get("/me")
def get_me(claims: Annotated[dict, Depends(current_user)]):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, role, created_at
                FROM users
                WHERE id = %s
                """,
                (claims["sub"],),
            )
            user = cursor.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@app.get("/users")
def list_users(_: Annotated[dict, Depends(current_user)]):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, role, created_at
                FROM users
                ORDER BY created_at ASC
                """
            )
            users = cursor.fetchall()
    return {"users": users}
