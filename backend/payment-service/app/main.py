from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from shared.auth import require_user_claims
from shared.config import get_settings
from shared.database import check_database, get_connection
from shared.metrics import MetricsMiddleware, metrics_response

settings = get_settings()
app = FastAPI(title="Payment Service", version="1.0.0")
app.add_middleware(MetricsMiddleware, service_name=settings.service_name)


class CreatePaymentRequest(BaseModel):
    order_id: str
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    method: Literal["card", "cash", "demo"] = "demo"


def current_user(authorization: Annotated[str | None, Header()] = None):
    return require_user_claims(settings.jwt_secret_key, authorization)


def normalize_payment(payment: dict) -> dict:
    if isinstance(payment.get("amount"), Decimal):
        payment["amount"] = float(payment["amount"])
    return payment


def run_health_check():
    check_database(settings.database_url)


@app.get("/health")
def health():
    run_health_check()
    return {"service": settings.service_name, "status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response(settings.service_name, run_health_check)


@app.post("/payments", status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: CreatePaymentRequest,
    claims: Annotated[dict, Depends(current_user)],
):
    payment_id = str(uuid4())

    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, total_price, status
                FROM orders
                WHERE id = %s AND user_id = %s
                """,
                (payload.order_id, claims["sub"]),
            )
            order = cursor.fetchone()

            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found.",
                )

            order_total = Decimal(order["total_price"])
            if payload.amount != order_total:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment amount must match the order total.",
                )

            cursor.execute(
                """
                INSERT INTO payments (id, order_id, user_id, amount, method, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, order_id, user_id, amount, method, status, created_at
                """,
                (
                    payment_id,
                    payload.order_id,
                    claims["sub"],
                    payload.amount,
                    payload.method,
                    "authorized",
                ),
            )
            payment = cursor.fetchone()

            cursor.execute(
                """
                UPDATE orders
                SET status = %s
                WHERE id = %s AND user_id = %s
                """,
                ("paid", payload.order_id, claims["sub"]),
            )
        connection.commit()

    return normalize_payment(payment)


@app.get("/payments")
def list_payments(claims: Annotated[dict, Depends(current_user)]):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, order_id, user_id, amount, method, status, created_at
                FROM payments
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (claims["sub"],),
            )
            payments = [normalize_payment(payment) for payment in cursor.fetchall()]
    return {"payments": payments}
