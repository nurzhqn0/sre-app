#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict


PATTERNS = {
    "database_connection": re.compile(
        r"database|psycopg|connection refused|could not connect|connection failed",
        re.IGNORECASE,
    ),
    "dns_or_endpoint": re.compile(
        r"could not translate host name|temporary failure in name resolution|"
        r"name or service not known|nodename nor servname|postgres-broken",
        re.IGNORECASE,
    ),
    "http_5xx": re.compile(r"\b5\d\d\b|internal server error|bad gateway", re.IGNORECASE),
    "restart_loop": re.compile(
        r"restart|restarting|exited with code|unhealthy|healthcheck", re.IGNORECASE
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan Docker Compose logs for SRE clues.")
    parser.add_argument("--tail", type=int, default=300)
    parser.add_argument("--fail-on-findings", action="store_true")
    parser.add_argument("services", nargs="*", help="Optional Compose service names.")
    return parser.parse_args()


def collect_logs(tail: int, services: list[str]) -> str:
    command = ["docker", "compose", "logs", "--no-color", "--tail", str(tail)]
    command.extend(services)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def main() -> int:
    args = parse_args()
    try:
        logs = collect_logs(args.tail, args.services)
    except Exception as exc:
        print(f"log inspection failed: {exc}")
        return 2

    findings: dict[str, list[str]] = defaultdict(list)
    for line in logs.splitlines():
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                findings[name].append(line)

    if not findings:
        print(f"no known failure patterns found in the last {args.tail} log lines")
        return 0

    print(f"failure patterns found in the last {args.tail} log lines:")
    for name in sorted(findings):
        print(f"\n{name}: {len(findings[name])} matches")
        for line in findings[name][:5]:
            print(f"- {line}")

    return 1 if args.fail_on_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
