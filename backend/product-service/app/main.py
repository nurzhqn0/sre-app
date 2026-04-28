from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI, HTTPException, status

from shared.config import get_settings
from shared.database import check_database, get_connection
from shared.metrics import MetricsMiddleware, metrics_response

settings = get_settings()
app = FastAPI(title="Product Service", version="1.0.0")
app.add_middleware(MetricsMiddleware, service_name=settings.service_name)


def normalize_product(product: dict) -> dict:
    if isinstance(product.get("price"), Decimal):
        product["price"] = float(product["price"])
    return product


@app.get("/health")
def health():
    check_database(settings.database_url)
    return {"service": settings.service_name, "status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.get("/products")
def list_products():
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, description, category, inventory, price
                FROM products
                ORDER BY name ASC
                """
            )
            products = [normalize_product(product) for product in cursor.fetchall()]
    return {"products": products}


@app.get("/products/{product_id}")
def get_product(product_id: str):
    with get_connection(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, description, category, inventory, price
                FROM products
                WHERE id = %s
                """,
                (product_id,),
            )
            product = cursor.fetchone()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return normalize_product(product)
