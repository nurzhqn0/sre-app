#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


APP_SERVICES = {
    "auth-service",
    "user-service",
    "product-service",
    "order-service",
    "chat-service",
}
HEALTHCHECK_SERVICES = APP_SERVICES | {"postgres", "frontend"}
EXPECTED_RESTART_POLICY = "unless-stopped"
ALLOWED_DATABASE_HOSTS = {"postgres"}
REQUIRED_ALERTS = {
    "ServiceHealthUnhealthy",
    "ServiceTargetDown",
    "OrderServiceHealthUnhealthy",
    "OrderServiceTargetDown",
    "ServiceHigh5xxRate",
    "ServiceHighP95Latency",
    "OrderServiceHighCpuUsage",
    "ContainerRestartDetected",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Docker Compose configuration before deployment."
    )
    parser.add_argument(
        "-f",
        "--file",
        action="append",
        default=[],
        help="Compose file to include. Repeat for overrides.",
    )
    return parser.parse_args()


def run_compose_config(files: list[str]) -> dict[str, Any]:
    command = ["docker", "compose"]
    for file_name in files or ["docker-compose.yml"]:
        command.extend(["-f", file_name])
    command.extend(["config", "--format", "json"])

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def normalized_environment(service: dict[str, Any]) -> dict[str, str]:
    environment = service.get("environment") or {}
    if isinstance(environment, dict):
        return {str(key): str(value) for key, value in environment.items()}

    normalized: dict[str, str] = {}
    for item in environment:
        key, _, value = str(item).partition("=")
        normalized[key] = value
    return normalized


def validate_database_url(service_name: str, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    database_url = env.get("DATABASE_URL")
    if not database_url:
        errors.append(f"{service_name}: DATABASE_URL is missing.")
        return errors

    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        errors.append(f"{service_name}: DATABASE_URL must use postgresql scheme.")
    if parsed.hostname not in ALLOWED_DATABASE_HOSTS:
        errors.append(
            f"{service_name}: DATABASE_URL host '{parsed.hostname}' is not allowed; "
            "expected postgres."
        )
    if not parsed.username or not parsed.password or not parsed.path.strip("/"):
        errors.append(
            f"{service_name}: DATABASE_URL must include user, password, and database."
        )
    return errors


def validate_service_config(compose: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    services = compose.get("services") or {}

    expected_services = APP_SERVICES | {
        "postgres",
        "prometheus",
        "grafana",
        "frontend",
        "cadvisor",
    }
    missing = sorted(expected_services - set(services))
    if missing:
        errors.append(f"Missing services: {', '.join(missing)}.")

    for service_name, service in services.items():
        if service.get("restart") != EXPECTED_RESTART_POLICY:
            errors.append(
                f"{service_name}: restart policy must be {EXPECTED_RESTART_POLICY}."
            )

    for service_name in sorted(HEALTHCHECK_SERVICES):
        if service_name in services and not services[service_name].get("healthcheck"):
            errors.append(f"{service_name}: healthcheck is missing.")

    for service_name in sorted(APP_SERVICES):
        if service_name not in services:
            continue
        env = normalized_environment(services[service_name])
        for key in ("SERVICE_NAME", "PORT", "DATABASE_URL", "JWT_SECRET_KEY"):
            if not env.get(key):
                errors.append(f"{service_name}: {key} is missing.")
        errors.extend(validate_database_url(service_name, env))

        if service_name == "order-service":
            product_url = env.get("PRODUCT_SERVICE_URL", "")
            parsed = urlparse(product_url)
            if parsed.hostname != "product-service":
                errors.append(
                    "order-service: PRODUCT_SERVICE_URL must target product-service."
                )

    return errors


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def validate_monitoring_files() -> list[str]:
    errors: list[str] = []
    prometheus = read_text("monitoring/prometheus/prometheus.yml")
    alerts = read_text("monitoring/prometheus/alerts.yml")

    if "/etc/prometheus/alerts.yml" not in prometheus:
        errors.append("prometheus.yml: alert rule file is not configured.")
    if "cadvisor:8080" not in prometheus:
        errors.append("prometheus.yml: cadvisor scrape target is missing.")

    for alert_name in sorted(REQUIRED_ALERTS):
        if f"alert: {alert_name}" not in alerts:
            errors.append(f"alerts.yml: {alert_name} is missing.")

    return errors


def main() -> int:
    args = parse_args()
    try:
        compose = run_compose_config(args.file)
        errors = validate_service_config(compose) + validate_monitoring_files()
    except Exception as exc:
        print(f"configuration validation failed: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("configuration validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    files = ", ".join(args.file or ["docker-compose.yml"])
    print(f"configuration validation passed for {files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
