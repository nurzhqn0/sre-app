#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE_PREFIX="${STACK_IMAGE_PREFIX:-sre-app}"

docker build -t "${IMAGE_PREFIX}/auth-service:latest" -f "${ROOT_DIR}/backend/auth-service/Dockerfile" "${ROOT_DIR}"
docker build -t "${IMAGE_PREFIX}/user-service:latest" -f "${ROOT_DIR}/backend/user-service/Dockerfile" "${ROOT_DIR}"
docker build -t "${IMAGE_PREFIX}/product-service:latest" -f "${ROOT_DIR}/backend/product-service/Dockerfile" "${ROOT_DIR}"
docker build -t "${IMAGE_PREFIX}/order-service:latest" -f "${ROOT_DIR}/backend/order-service/Dockerfile" "${ROOT_DIR}"
docker build -t "${IMAGE_PREFIX}/chat-service:latest" -f "${ROOT_DIR}/backend/chat-service/Dockerfile" "${ROOT_DIR}"
docker build -t "${IMAGE_PREFIX}/frontend:latest" -f "${ROOT_DIR}/frontend/Dockerfile" "${ROOT_DIR}"
echo "Built stack images with prefix ${IMAGE_PREFIX}"
