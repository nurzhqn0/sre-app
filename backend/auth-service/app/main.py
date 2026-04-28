from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from shared.auth import create_access_token, hash_password, verify_password
from shared.config import get_settings
from shared.database import check_database, get_connection
from shared.metrics import MetricsMiddleware, metrics_response

settings = get_settings()
app = FastAPI(title="Auth Service", version="1.0.0")
app.add_middleware(MetricsMiddleware, service_name=settings.service_name)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    check_database(settings.database_url)
    return {"service": settings.service_name, "status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM users
                WHERE username = %s OR email = %s
                """,
                (payload.username, payload.email.lower()),
            )
            existing_user = cursor.fetchone()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this username or email already exists.",
                )

            user_id = str(uuid4())
            cursor.execute(
                """
                INSERT INTO users (id, username, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, username, email, role, created_at
                """,
                (
                    user_id,
                    payload.username,
                    payload.email.lower(),
                    hash_password(payload.password),
                    "customer",
                ),
            )
            user = cursor.fetchone()
        connection.commit()

    access_token = create_access_token(
        secret_key=settings.jwt_secret_key,
        subject=user["id"],
        username=user["username"],
        role=user["role"],
    )
    return {"access_token": access_token, "user": user}


@app.post("/login")
def login_user(payload: LoginRequest):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, password_hash, role, created_at
                FROM users
                WHERE username = %s
                """,
                (payload.username,),
            )
            user = cursor.fetchone()

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    access_token = create_access_token(
        secret_key=settings.jwt_secret_key,
        subject=user["id"],
        username=user["username"],
        role=user["role"],
    )
    public_user = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"],
    }
    return {"access_token": access_token, "user": public_user}
