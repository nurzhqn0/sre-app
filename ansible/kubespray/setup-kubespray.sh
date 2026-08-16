#!/usr/bin/env bash
# Quickstart script to provision Kubernetes cluster with Kubespray

set -euo pipefail

KUBESPRAY_VERSION="${KUBESPRAY_VERSION:-v2.26.0}"
WORKSPACE_DIR="$(cd "$(dirname "$0")" && pwd)"
KUBESPRAY_DIR="${WORKSPACE_DIR}/vendor-kubespray"

echo "=== Kubespray Cluster Setup Tool ==="

if [ ! -d "${KUBESPRAY_DIR}" ]; then
  echo "Cloning Kubespray ${KUBESPRAY_VERSION}..."
  git clone --depth 1 --branch "${KUBESPRAY_VERSION}" https://github.com/kubernetes-sigs/kubespray.git "${KUBESPRAY_DIR}"
fi

echo "Installing Kubespray Python requirements..."
python3 -m pip install -r "${KUBESPRAY_DIR}/requirements.txt"

INVENTORY_FILE="${WORKSPACE_DIR}/inventory.ini"
if [ ! -f "${INVENTORY_FILE}" ]; then
  echo "No inventory.ini found. Copying from inventory.ini.example..."
  cp "${WORKSPACE_DIR}/inventory.ini.example" "${INVENTORY_FILE}"
  echo "Please edit ${INVENTORY_FILE} with your servers' actual IP addresses and run this script again."
  exit 0
fi

echo "Running Kubespray Ansible playbook..."
ansible-playbook -i "${INVENTORY_FILE}" -b -v "${KUBESPRAY_DIR}/cluster.yml"

echo "=== Kubernetes Cluster Provisioned Successfully! ==="
echo "You can copy the kubeconfig from master node (~/.kube/config) and deploy sre-app:"
echo "  kubectl apply -f k8s/00-namespace-config.yaml"
echo "  kubectl apply -f k8s/10-postgres.yaml"
echo "  kubectl apply -f k8s/15-redis.yaml"
echo "  kubectl apply -f k8s/20-services.yaml"
echo "  kubectl apply -f k8s/30-frontend.yaml"
echo "  kubectl apply -f k8s/50-frontend-ingress-nginx.yaml"
