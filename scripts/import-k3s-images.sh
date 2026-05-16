#!/usr/bin/env bash

set -euo pipefail

IMAGE_PREFIX="${STACK_IMAGE_PREFIX:-sre-app}"

images=(
  auth-service
  user-service
  product-service
  order-service
  chat-service
  payment-service
  frontend
)

for image in "${images[@]}"; do
  full_image="${IMAGE_PREFIX}/${image}:latest"
  echo "Importing ${full_image} into k3s containerd"
  docker save "${full_image}" | k3s ctr images import -
done

echo "Imported ${#images[@]} images into k3s containerd"
