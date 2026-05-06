#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_PASSWORD = "LoadTestPassword123!"


@dataclass(frozen=True)
class Result:
    status: int
    duration: float
    error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate order-service load.")
    parser.add_argument("--base-url", default="http://localhost")
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--username", default="")
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--quantity", type=int, default=1)
    return parser.parse_args()


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 10.0,
) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read().decode("utf-8")
            return response.status, json.loads(data) if data else {}
    except urllib.error.HTTPError as exc:
        data = exc.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        return exc.code, parsed


def register_or_login(base_url: str, username: str, password: str) -> str:
    email = f"{username}@example.com"
    status, payload = request_json(
        "POST",
        f"{base_url}/api/auth/register",
        {"username": username, "email": email, "password": password},
    )
    if status == 201:
        return str(payload["access_token"])
    if status != 409:
        raise RuntimeError(f"registration failed with status {status}: {payload}")

    status, payload = request_json(
        "POST",
        f"{base_url}/api/auth/login",
        {"username": username, "password": password},
    )
    if status != 200:
        raise RuntimeError(f"login failed with status {status}: {payload}")
    return str(payload["access_token"])


def first_product_id(base_url: str) -> str:
    status, payload = request_json("GET", f"{base_url}/api/products/products")
    if status != 200:
        raise RuntimeError(f"product lookup failed with status {status}: {payload}")
    products = payload.get("products") or []
    if not products:
        raise RuntimeError("product lookup returned no products")
    return str(products[0]["id"])


def create_order(base_url: str, token: str, product_id: str, quantity: int) -> Result:
    start = time.perf_counter()
    try:
        status, payload = request_json(
            "POST",
            f"{base_url}/api/orders/orders",
            {"product_id": product_id, "quantity": quantity},
            token=token,
        )
        duration = time.perf_counter() - start
        error = None if 200 <= status < 300 else json.dumps(payload)
        return Result(status=status, duration=duration, error=error)
    except Exception as exc:
        return Result(status=0, duration=time.perf_counter() - start, error=str(exc))


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))
    return ordered[index]


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    username = args.username or f"loadtest_{int(time.time())}"

    token = register_or_login(base_url, username, args.password)
    product_id = first_product_id(base_url)

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.users) as executor:
        futures = [
            executor.submit(
                create_order,
                base_url,
                token,
                product_id,
                args.quantity,
            )
            for _ in range(args.requests)
        ]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    elapsed = time.perf_counter() - started

    success_count = sum(1 for result in results if 200 <= result.status < 300)
    error_count = len(results) - success_count
    durations = [result.duration for result in results]
    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[str(result.status)] = status_counts.get(str(result.status), 0) + 1

    summary = {
        "base_url": base_url,
        "username": username,
        "requests": len(results),
        "concurrency": args.users,
        "success_count": success_count,
        "error_count": error_count,
        "error_rate": round(error_count / max(len(results), 1), 4),
        "rps": round(len(results) / elapsed, 2) if elapsed > 0 else 0,
        "p95_seconds": round(percentile(durations, 0.95), 4),
        "p99_seconds": round(percentile(durations, 0.99), 4),
        "status_counts": status_counts,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    sample_errors = [result.error for result in results if result.error][:5]
    if sample_errors:
        print("sample_errors:")
        for error in sample_errors:
            print(f"- {error}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
