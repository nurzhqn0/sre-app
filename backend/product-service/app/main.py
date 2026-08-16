import json
import logging
from decimal import Decimal

from fastapi import FastAPI, HTTPException, status

from shared.config import get_settings
from shared.database import check_database, get_connection
from shared.metrics import MetricsMiddleware, metrics_response
from shared.redis_client import check_redis, get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()
app = FastAPI(title="Product Service", version="1.0.0")
app.add_middleware(MetricsMiddleware, service_name=settings.service_name)

CACHE_TTL_SECONDS = 60


def normalize_product(product: dict) -> dict:
    if isinstance(product.get("price"), Decimal):
        product["price"] = float(product["price"])
    return product


def run_health_check():
    check_database(settings.database_url)


@app.get("/health")
def health():
    run_health_check()
    redis_healthy = check_redis(settings.redis_url)
    return {
        "service": settings.service_name,
        "status": "ok",
        "database": "connected",
        "redis": "connected" if redis_healthy else "degraded",
    }


@app.get("/metrics")
def metrics():
    return metrics_response(settings.service_name, run_health_check)


@app.get("/products")
def list_products():
    cache_key = "products:catalog"
    try:
        r = get_redis_client(settings.redis_url)
        cached = r.get(cache_key)
        if cached:
            return {"products": json.loads(cached), "cached": True}
    except Exception as exc:
        logger.debug("Redis cache read failed: %s", exc)

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

    try:
        r = get_redis_client(settings.redis_url)
        r.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(products))
    except Exception as exc:
        logger.debug("Redis cache write failed: %s", exc)

    return {"products": products, "cached": False}


@app.get("/products/{product_id}")
def get_product(product_id: str):
    cache_key = f"product:{product_id}"
    try:
        r = get_redis_client(settings.redis_url)
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as exc:
        logger.debug("Redis cache read failed: %s", exc)

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
    normalized = normalize_product(product)

    try:
        r = get_redis_client(settings.redis_url)
        r.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(normalized))
    except Exception as exc:
        logger.debug("Redis cache write failed: %s", exc)

    return normalized

