# Deployment and Architecture Guide: Kubespray, GitLab CI/CD, Redis & Nginx

This guide covers:
1. **Kubernetes Cluster Setup using Kubespray**
2. **GitLab CI/CD Pipeline (Build, Push to Registry, Deploy)**
3. **Redis In-Memory Caching & Architecture**
4. **API Health Checks and Observability**
5. **NGINX Ingress vs Alternatives**

---

## 1. Kubernetes Cluster Setup with Kubespray

[Kubespray](https://github.com/kubernetes-sigs/kubespray) is an official Kubernetes SIGs project providing Ansible playbooks for provisioning production-grade, highly-available Kubernetes clusters across bare metal, OpenStack, AWS, GCP, or VMware.

### Quickstart

1. Configure your target nodes in `ansible/kubespray/inventory.ini`:
   ```bash
   cp ansible/kubespray/inventory.ini.example ansible/kubespray/inventory.ini
   # Edit IP addresses and SSH keys
   vim ansible/kubespray/inventory.ini
   ```

2. Run the helper script:
   ```bash
   ./ansible/kubespray/setup-kubespray.sh
   ```
   Or execute directly with Ansible:
   ```bash
   ansible-playbook -i ansible/kubespray/inventory.ini -b -v vendor-kubespray/cluster.yml
   ```

3. Obtain `kubeconfig`:
   ```bash
   ssh ubuntu@<master-node-ip> "sudo cat /etc/kubernetes/admin.conf" > ~/.kube/config
   kubectl get nodes -o wide
   ```

---

## 2. GitLab CI/CD Pipeline

The `.gitlab-ci.yml` pipeline automates the entire lifecycle:

```
[test] ───────────► [build-and-push] ───────────► [deploy] ───────────► [healthcheck]
├── validate:python ├── build:auth-service       ├── deploy:k8s         └── healthcheck:verify
├── validate:front  ├── build:user-service       └── deploy:ansible
├── validate:k8s    ├── build:product-service
└── validate:ans    ├── build:order-service
                    ├── build:chat-service
                    ├── build:payment-service
                    └── build:frontend
```

### GitLab CI/CD Variables to Configure

In your GitLab project under **Settings > CI/CD > Variables**:

| Variable | Description | Example |
|---|---|---|
| `KUBE_CONFIG` | Base64-encoded or raw `kubeconfig` content | `apiVersion: v1...` |
| `APP_DOMAIN` | Target production domain | `sre.yourdomain.com` |
| `USE_NGINX_INGRESS` | Set to `true` to use NGINX Ingress Controller | `true` |
| `VPS_HOST` | (Optional) Host IP for Ansible SSH deployment | `209.38.220.131` |
| `VPS_USER` | (Optional) SSH username | `root` or `ubuntu` |
| `VPS_SSH_PRIVATE_KEY` | (Optional) Private SSH key | `-----BEGIN OPENSSH...` |

---

## 3. Redis In-Memory Storage & Caching

Redis is integrated as an in-memory cache and session/broker store:

- **Docker Compose**: Service `redis` with `redis:7-alpine` on port `6379`.
- **Kubernetes**: Deployment and Service defined in `k8s/15-redis.yaml`.
- **Application Integration**:
  - `product-service` caches product catalogs with automatic fallback to PostgreSQL.
  - `/health` endpoint checks both database and Redis connectivity.

---

## 4. API Healthchecks & Probes

Each microservice exposes standardized endpoints:

- `GET /health`: Returns JSON with service name and subsystem connectivity status:
  ```json
  {
    "service": "product-service",
    "status": "ok",
    "database": "connected",
    "redis": "connected"
  }
  ```
- `GET /metrics`: Returns Prometheus metrics including `service_health_status{service="..."} 1`.
- **Kubernetes Probes**:
  - `livenessProbe`: Restart container if the service deadlocks.
  - `readinessProbe`: Remove pod from traffic routing if database or dependencies fail.

---

## 5. Nginx & Ingress Options

| Layer | Component | Function |
|---|---|---|
| **Frontend Container** | **Nginx** (`frontend/nginx/default.conf`) | Serves React static files and routes `/api/*` and `/ws/*` internally. |
| **K8s Ingress (Option A)** | **NGINX Ingress Controller** (`k8s/50-frontend-ingress-nginx.yaml`) | Default in Kubespray; handles SSL termination via cert-manager. |
| **K8s Ingress (Option B)** | **Traefik Ingress** (`k8s/50-frontend-ingress.yaml`) | Default in k3s. |

### Applying to Kubernetes

```bash
# 1. Apply namespace, configs, secrets
kubectl apply -f k8s/00-namespace-config.yaml

# 2. Deploy Postgres and Redis
kubectl apply -f k8s/10-postgres.yaml
kubectl apply -f k8s/15-redis.yaml

# 3. Deploy all microservices and frontend
kubectl apply -f k8s/20-services.yaml
kubectl apply -f k8s/30-frontend.yaml

# 4. Deploy Prometheus & Grafana monitoring
kubectl apply -f k8s/40-monitoring.yaml
kubectl apply -f k8s/45-grafana-dashboard.yaml

# 5. Apply Ingress (NGINX Ingress for Kubespray)
kubectl apply -f k8s/50-frontend-ingress-nginx.yaml
```
