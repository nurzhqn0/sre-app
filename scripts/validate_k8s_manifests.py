#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: 'PyYAML' is not installed. Please install it with 'pip install pyyaml'.", file=sys.stderr)
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Kubernetes YAML manifests for syntax and basic resource structure."
    )
    parser.add_argument(
        "--path",
        "-p",
        default="k8s",
        help="Directory containing Kubernetes manifests (default: k8s).",
    )
    return parser.parse_args()


def validate_manifests(target_dir: str) -> tuple[int, int, list[str]]:
    pattern_yaml = f"{target_dir}/**/*.yaml"
    pattern_yml = f"{target_dir}/**/*.yml"
    files = sorted(set(glob.glob(pattern_yaml, recursive=True) + glob.glob(pattern_yml, recursive=True)))

    errors: list[str] = []
    total_docs = 0

    for file_path in files:
        path = Path(file_path)
        try:
            content = path.read_text(encoding="utf-8")
            docs = list(yaml.safe_load_all(content))
            for idx, doc in enumerate(docs, start=1):
                if doc is None:
                    continue
                total_docs += 1
                if not isinstance(doc, dict):
                    errors.append(f"{file_path} (doc #{idx}): Expected mapping/dict, found {type(doc).__name__}")
                    continue
                if "kind" not in doc or "apiVersion" not in doc:
                    errors.append(f"{file_path} (doc #{idx}): Missing 'kind' or 'apiVersion' field")
        except Exception as exc:
            errors.append(f"{file_path}: YAML parsing error: {exc}")

    return len(files), total_docs, errors


def main() -> int:
    args = parse_args()
    file_count, doc_count, errors = validate_manifests(args.path)

    if errors:
        print(f"Kubernetes manifest validation failed ({len(errors)} error(s)):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"Validated {file_count} Kubernetes YAML files ({doc_count} resources) successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
