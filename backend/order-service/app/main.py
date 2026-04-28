from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from shared.auth import require_user_claims
from shared.config import get_settings
from shared.database import check_database, get_connection
from shared.metrics import MetricsMiddleware, metrics_response

settings = get_settings()
app = FastAPI(title="Order Service", version="1.0.0")
app.add_middleware(MetricsMiddleware, service_name=settings.service_name)


class CreateOrderRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=25)


def current_user(authorization: Annotated[str | None, Header()] = None):
    return require_user_claims(settings.jwt_secret_key, authorization)


def normalize_order(order: dict) -> dict:
    for key in ("unit_price", "total_price"):
        if isinstance(order.get(key), Decimal):
            order[key] = float(order[key])
    return order


def fetch_product(product_id: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.product_service_url}/products/{product_id}",
            timeout=5.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to validate product details.",
        ) from exc
    return response.json()


@app.get("/health")
def health():
    check_database(settings.database_url)
    return {"service": settings.service_name, "status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    payload: CreateOrderRequest,
    claims: Annotated[dict, Depends(current_user)],
):
    product = fetch_product(payload.product_id)
    unit_price = float(product["price"])
    total_price = round(unit_price * payload.quantity, 2)
    order_id = str(uuid4())

    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO orders (
                    id, user_id, product_id, product_name, quantity, unit_price, total_price, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, product_id, product_name, quantity, unit_price, total_price, status, created_at
                """,
                (
                    order_id,
                    claims["sub"],
                    product["id"],
                    product["name"],
                    payload.quantity,
                    unit_price,
                    total_price,
                    "created",
                ),
            )
            order = cursor.fetchone()
        connection.commit()

    return normalize_order(order)


@app.get("/orders")
def list_orders(claims: Annotated[dict, Depends(current_user)]):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, product_id, product_name, quantity, unit_price, total_price, status, created_at
                FROM orders
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (claims["sub"],),
            )
            orders = [normalize_order(order) for order in cursor.fetchall()]
    return {"orders": orders}


@app.get("/orders/{order_id}")
def get_order(order_id: str, claims: Annotated[dict, Depends(current_user)]):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, product_id, product_name, quantity, unit_price, total_price, status, created_at
                FROM orders
                WHERE id = %s AND user_id = %s
                """,
                (order_id, claims["sub"]),
            )
            order = cursor.fetchone()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    return normalize_order(order)
