# End-to-End SRE Implementation for a Multi-Orchestrated Microservices System

## 1. Abstract

This project implements Site Reliability Engineering practices across a distributed microservices platform. The system uses six independent FastAPI backend services, a React frontend served by Nginx, PostgreSQL, Docker Compose, Docker Swarm, Kubernetes, Terraform, Ansible, Prometheus, Grafana, and incident-response documentation.

The project demonstrates the full SRE lifecycle: service design, containerization, orchestration, infrastructure provisioning, configuration automation, SLIs/SLOs, monitoring, alerting, incident simulation, postmortem analysis, and capacity planning.

Git repository: <https://github.com/nurzhqn0/sre-app.git>

Live deployment:

- Direct IP: <http://209.38.220.131/>
- Domain target: <https://sre.nurzhqn.com/>
- Current platform: Kubernetes on k3s with Traefik Ingress

Current Kubernetes deployment state:

- namespace: `sre-app`
- cluster: single-node k3s VPS
- ingress: `frontend` routes `sre.nurzhqn.com` on HTTPS port `443`
- TLS: cert-manager issues and renews a Let's Encrypt certificate in the `frontend-tls` secret
- frontend service: internal `ClusterIP` behind Traefik
- running pods: `auth-service`, `user-service`, `product-service`, `order-service`, `payment-service`, `chat-service`, `frontend`, `postgres`, `prometheus`, and `grafana`
- verification: `curl -I https://sre.nurzhqn.com/` returns `HTTP/1.1 200 OK` or `HTTP/2 200` after DNS resolves
- ingress verification before DNS propagation: `curl -I --resolve sre.nurzhqn.com:443:127.0.0.1 https://sre.nurzhqn.com/`
- DNS requirement: public DNS must resolve `sre.nurzhqn.com` to `209.38.220.131`

## 2. Objectives

- Deploy a distributed microservices architecture with six backend services.
- Demonstrate Docker Compose, Docker Swarm, and Kubernetes deployment models.
- Provision cloud infrastructure with Terraform.
- Automate setup and deployment with Ansible.
- Define and monitor SLIs/SLOs for availability, latency, error rate, and success rate.
- Simulate an order-service production incident and document response.
- Provide automation and capacity planning evidence for reliability improvements.

## 3. System Overview

The application is an e-commerce style reliability demo.

Backend microservices:

| Service | Responsibility | Port |
| --- | --- | --- |
| `auth-service` | User registration, login, JWT issuing | `8001` |
| `user-service` | User profile and user listing | `8002` |
| `product-service` | Product catalog reads | `8003` |
| `order-service` | Order creation and listing | `8004` |
| `chat-service` | WebSocket operations chat and message history | `8005` |
| `payment-service` | Simulated payment authorization for orders | `8006` |

Supporting components:

- `frontend`: React UI served by Nginx on port `80`.
- `postgres`: relational persistence for users, products, orders, messages, and payments.
- `prometheus`: metrics collection and alert evaluation.
- `grafana`: dashboard visualization.
- `cadvisor`: container CPU, memory, and restart metrics for Docker Compose and Swarm.

## 3.1 Ports and Access

| Component | Internal Port | Docker Compose Access | Docker Swarm Access | Kubernetes Access | Live VPS Access |
| --- | ---: | --- | --- | --- | --- |
| `frontend` | `80` | `http://localhost` | `http://SERVER_IP` or `STACK_HTTP_PORT` | Traefik Ingress to `ClusterIP` service port `80` with TLS on `443` | `https://sre.nurzhqn.com/` when DNS resolves |
| `auth-service` | `8001` | via frontend `/api/auth/` | internal overlay network | `ClusterIP` `8001` | internal only |
| `user-service` | `8002` | via frontend `/api/users/` | internal overlay network | `ClusterIP` `8002` | internal only |
| `product-service` | `8003` | via frontend `/api/products/` | internal overlay network | `ClusterIP` `8003` | internal only |
| `order-service` | `8004` | via frontend `/api/orders/` | internal overlay network | `ClusterIP` `8004` | internal only |
| `chat-service` | `8005` | via frontend `/api/chat/` and `/ws/chat` | internal overlay network | `ClusterIP` `8005` | internal only |
| `payment-service` | `8006` | via frontend `/api/payments/` | internal overlay network | `ClusterIP` `8006` | internal only |
| `postgres` | `5432` | internal Docker network | internal overlay network | `ClusterIP` `5432` | internal only |
| `prometheus` | `9090` | `http://localhost:9090` | private via SSH tunnel to Swarm port `9091` | `ClusterIP` `9090`, access by SSH tunnel/port-forward only | private only |
| `grafana` | `3000` | `http://localhost:3000` | private via SSH tunnel to Swarm port `3001` | `ClusterIP` `3000`, access by SSH tunnel/port-forward only | private only |
| `cadvisor` | `8080` | internal Prometheus scrape target | internal/global Swarm scrape target | optional manifest only | not required |

Live VPS firewall:

- `22/tcp`: SSH
- `80/tcp`: HTTP challenge and optional redirect path through Traefik Ingress
- `443/tcp`: HTTPS frontend through Traefik Ingress
- Grafana and Prometheus are not exposed publicly

Recommended production-style access:

- expose only frontend on `80/tcp` and `443/tcp`
- keep Grafana and Prometheus private
- access monitoring from the laptop through SSH tunnels:

```bash
ssh \
  -L 3000:10.43.33.217:3000 \
  -L 9090:10.43.157.187:9090 \
  root@209.38.220.131
```

After opening the tunnel, use:

- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

## 4. Architecture

```text
User
  |
Frontend / Nginx
  |
  +--> auth-service
  +--> user-service
  +--> product-service
  +--> order-service --> product-service
  +--> payment-service --> PostgreSQL
  +--> chat-service
  |
PostgreSQL

Prometheus --> Grafana
Terraform --> VM provisioning
Ansible --> host setup and deployment
Docker Swarm + Kubernetes --> orchestration demonstrations
```

## 5. Orchestration

### Docker Compose

`docker-compose.yml` provides the primary local development and demo deployment. It includes health checks, restart policies, service dependencies, local-only monitoring ports, and all six backend microservices.

Validation command:

```bash
python3 scripts/validate_compose_config.py -f docker-compose.yml
```

Deployment command:

```bash
docker compose up -d --build
```

### Docker Swarm

`docker-stack.yml` provides the Swarm deployment model. It uses overlay networking, stack configs for Prometheus/Grafana/PostgreSQL initialization, and published ports for frontend and monitoring.

Deployment commands:

```bash
docker swarm init
./scripts/build-stack-images.sh
docker stack deploy -c docker-stack.yml sre-app
```

Capacity variant:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.capacity.yml sre-app
```

### Kubernetes

The `k8s/` directory provides local/demo-ready manifests for:

- namespace, secrets, and config maps
- PostgreSQL with initialization SQL
- deployments and services for frontend and all six backend services
- Prometheus and Grafana, with optional cAdvisor for compatible local clusters

Deployment:

```bash
kubectl apply -f k8s/
```

Local access:

```bash
kubectl -n sre-app port-forward svc/frontend 8080:80
kubectl -n sre-app port-forward svc/prometheus 9090:9090
kubectl -n sre-app port-forward svc/grafana 3000:3000
```

Live VPS access:

- <https://sre.nurzhqn.com/>

The live server uses k3s and Traefik Ingress. The `frontend` service stays internal as `ClusterIP`, while HTTPS port `443` is routed through `k8s/50-frontend-ingress.yaml`. cert-manager uses `k8s/60-cert-manager-issuer.yaml` to request a Let's Encrypt certificate.

## 6. Infrastructure as Code

Terraform files in `infra/terraform/` provision a DigitalOcean droplet and firewall. The firewall exposes SSH plus frontend HTTP/HTTPS while keeping monitoring private for SSH tunnel access.

Key files:

- `main.tf`
- `variables.tf`
- `outputs.tf`
- `terraform.tfvars.example`

Workflow:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
terraform output droplet_public_ip
```

## 7. Configuration Management and Automation

Ansible automation is stored in `ansible/`.

Files:

- `inventory.ini`: localhost/single-VM inventory.
- `site.yml`: installs Docker dependencies on Debian hosts, validates compose configuration, deploys the stack, and prints status.
- `k8s.yml`: applies Kubernetes manifests when `kubectl` is available.

Commands:

```bash
ansible-playbook -i ansible/inventory.ini ansible/site.yml
ansible-playbook -i ansible/inventory.ini ansible/k8s.yml
```

### 7.1 CI/CD Pipeline

The repository includes a GitHub Actions workflow at `.github/workflows/ci-cd.yml`.

CI runs on pull requests, pushes, and manual dispatch. It validates backend syntax, frontend lint/build, Docker Compose configuration, project deployment validation, Kubernetes YAML parsing, Ansible syntax, and Docker image builds.

CD runs only after CI succeeds on a `main` branch push or manual dispatch. The deployment job connects to the live VPS over SSH, creates a temporary Ansible inventory in the runner, and runs `ansible/k8s.yml`. The playbook checks out the exact Git commit on the VPS, builds images locally, imports them into k3s, applies manifests, restarts deployments, waits for rollout status, and prints workload status.

Required GitHub secrets:

| Secret | Purpose |
| --- | --- |
| `VPS_HOST` | VPS public IP |
| `VPS_USER` | SSH user |
| `VPS_SSH_PRIVATE_KEY` | Private SSH key for deployment |
| `VPS_SSH_PORT` | Optional SSH port, default `22` |

Optional GitHub variables:

| Variable | Default |
| --- | --- |
| `APP_DOMAIN` | `sre.nurzhqn.com` |
| `DEPLOY_PATH` | `/opt/sre-app` |
| `ACME_EMAIL` | `admin@sre.nurzhqn.com` |

## 8. SLIs and SLOs

SLIs:

- Availability: service health and scrape availability.
- Latency: HTTP request duration histogram.
- Error rate: 5xx response rate.
- Request success rate: successful requests divided by total requests.

SLOs:

| SLI | SLO |
| --- | --- |
| Availability | `>= 99%` |
| Latency | p95 `<= 200 ms` for normal demo traffic |
| Error rate | `<= 1%` |
| Request success rate | `>= 99%` |

Prometheus metrics are exposed by each backend service at `/metrics` through shared middleware.

## 9. Monitoring and Alerting

Prometheus configuration:

- `monitoring/prometheus/prometheus.yml`
- `monitoring/prometheus/prometheus-stack.yml`
- `monitoring/prometheus/alerts.yml`

Grafana configuration:

- `monitoring/grafana/provisioning/datasources/datasource.yml`
- `monitoring/grafana/provisioning/dashboards/dashboard.yml`
- `monitoring/grafana/dashboards/platform-overview.json`
- `k8s/45-grafana-dashboard.yaml` provisions the same dashboard in Kubernetes Grafana.

Alert coverage includes:

- unhealthy service health metric
- down Prometheus scrape targets
- high 5xx rate
- high p95 latency
- high order-service CPU usage
- container restart detection

## 10. Incident Simulation and Postmortem

Incident scenario: `order-service` receives an invalid PostgreSQL hostname through an override file.

### Docker Compose

Inject incident:

```bash
docker compose -f docker-compose.yml -f docker-compose.incident.yml up -d order-service
```

Expected impact:

- order creation and order listing fail
- `order-service` health check fails
- Prometheus target and health metrics show degradation
- Grafana dashboard shows order-service impact

Recovery:

```bash
docker compose up -d order-service
```

### Kubernetes

Inject the same incident in Kubernetes by applying a deployment patch for `order-service`:

```bash
kubectl apply -f k8s/incident/order-service-broken-db.yaml
kubectl -n sre-app rollout status deployment/order-service --timeout=90s
```

Expected Kubernetes impact:

- order creation and order listing fail
- `order-service` readiness fails because `/health` cannot connect to PostgreSQL
- rollout status times out or reports progress deadline exceeded
- Prometheus target and health metrics show degradation
- Grafana dashboard shows order-service impact

Kubernetes recovery:

```bash
kubectl apply -f k8s/20-services.yaml
kubectl -n sre-app rollout status deployment/order-service --timeout=120s
```

Kubernetes evidence commands:

```bash
kubectl -n sre-app get pods -l app=order-service
kubectl -n sre-app logs deployment/order-service --tail=100
kubectl -n sre-app get endpoints order-service
```

Detailed evidence and analysis:

- `docs/incident-report.md`
- `docs/postmortem.md`
- `docs/assignment-4-5-combined.md`

## 11. Capacity Planning

Capacity analysis focuses on order and payment workflows because they perform database writes and depend on existing user/order state.

Implemented strategies:

- health checks for frontend, database, and backend services
- restart policies for Docker Compose and Swarm
- Swarm capacity override with additional replicas for `order-service` and `payment-service`
- Prometheus CPU, memory, restart, error, and latency metrics
- load-generation script in `scripts/load_test.py`

Scaling guidance:

- scale `order-service` first when order latency or CPU pressure rises
- scale `payment-service` when authorization traffic increases
- tune PostgreSQL when database CPU, memory, or connection pressure becomes the bottleneck
- keep Grafana/Prometheus private and access them through SSH tunnels on remote hosts

## 12. Results

The final system demonstrates:

- six backend microservices and one Nginx-served frontend
- local Docker Compose deployment
- Docker Swarm deployment and scaling variant
- Kubernetes local deployment manifests
- Terraform infrastructure provisioning
- Ansible deployment automation
- Prometheus metrics and alert rules
- Grafana dashboard coverage
- incident simulation and postmortem analysis
- documented capacity planning and evidence checklist

## 13. Verification Checklist

Run these checks before final submission:

```bash
python3 scripts/validate_compose_config.py -f docker-compose.yml
cd frontend
npm run build
cd ..
kubectl apply --dry-run=client -f k8s/
ansible-playbook --syntax-check ansible/site.yml
ansible-playbook --syntax-check ansible/k8s.yml
```

GitHub Actions evidence:

- CI job passed on the final commit.
- Deployment job passed after CI.
- Deployment logs show successful Ansible rollout checks.
- `https://sre.nurzhqn.com/` returns the frontend when DNS resolves.
- If DNS is not ready, `curl --resolve sre.nurzhqn.com:443:209.38.220.131 https://sre.nurzhqn.com/` verifies the host-based Traefik Ingress.

Optional full local demo:

```bash
docker compose up -d --build
```

## 14. Screenshot and Evidence Guide

Use this section as the screenshot checklist for the final PDF. Replace each placeholder with the screenshot or terminal capture.

### 14.1 Live Frontend

How to capture:

1. Open `https://sre.nurzhqn.com/`.
2. Confirm the browser shows a valid HTTPS certificate.
3. Capture the main UI showing the application loaded.

Placeholder:

```text
[Screenshot: live frontend home page]
```

### 14.2 Product, Order, Payment, Chat Flow

How to capture:

1. Register or log in.
2. Open Products and show product catalog.
3. Open Orders and create an order.
4. Open Payments and authorize payment.
5. Open Chat and send one message.

Placeholders:

```text
[Screenshot: product catalog]
[Screenshot: created order]
[Screenshot: authorized payment]
[Screenshot: chat message]
```

### 14.3 Kubernetes Deployment

How to capture:

Run:

```bash
kubectl -n sre-app get pods
kubectl -n sre-app get svc
kubectl -n sre-app get ingress
```

Expected evidence:

- all core pods are `1/1 Running`
- frontend is exposed through Traefik Ingress
- Grafana and Prometheus are `ClusterIP`

Placeholder:

```text
[Screenshot or terminal output: Kubernetes pods/services/ingress]
```

### 14.4 Ingress and DNS Verification

How to capture:

Run on the VPS:

```bash
curl -I --resolve sre.nurzhqn.com:443:127.0.0.1 https://sre.nurzhqn.com
kubectl -n sre-app get certificate
kubectl -n sre-app get secret frontend-tls
```

Run from the laptop:

```bash
dig +short sre.nurzhqn.com
```

Expected:

- HTTPS endpoint returns `HTTP/1.1 200 OK` or `HTTP/2 200`
- Certificate status is ready and the `frontend-tls` secret exists
- DNS returns `209.38.220.131` after propagation

Placeholder:

```text
[Screenshot or terminal output: ingress and DNS checks]
```

### 14.5 Private Prometheus and Grafana Access

Grafana and Prometheus must not be exposed publicly. Access them through an SSH tunnel.

How to capture:

From laptop:

```bash
ssh \
  -L 3000:10.43.33.217:3000 \
  -L 9090:10.43.157.187:9090 \
  root@209.38.220.131
```

Then open locally:

```text
http://localhost:3000
http://localhost:9090
```

In Grafana, open:

```text
Dashboards -> SRE App -> SRE App Platform Overview
```

Placeholders:

```text
[Screenshot: Prometheus targets page on localhost:9090]
[Screenshot: Grafana SRE App Platform Overview dashboard on localhost:3000]
```

### 14.6 Monitoring Privacy Verification

How to capture:

Run on the VPS:

```bash
kubectl -n sre-app get svc grafana prometheus
ss -lntp | grep -E '30090|30300' || true
```

Expected:

- `grafana` is `ClusterIP`
- `prometheus` is `ClusterIP`
- no process listens on public NodePorts `30090` or `30300`

Placeholder:

```text
[Screenshot or terminal output: Grafana/Prometheus private service verification]
```

### 14.7 Incident Simulation

How to capture using Docker Compose demo:

Inject incident:

```bash
docker compose -f docker-compose.yml -f docker-compose.incident.yml up -d order-service
```

Capture:

```bash
docker compose logs order-service
curl -s 'http://localhost:9090/api/v1/query?query=service_health_status{service="order-service"}'
```

Recover:

```bash
docker compose up -d order-service
```

Placeholders:

```text
[Screenshot or terminal output: order-service incident]
[Screenshot or terminal output: order-service recovery]
```

### 14.8 Docker Swarm Evidence

How to capture:

```bash
docker swarm init
./scripts/build-stack-images.sh
docker stack deploy -c docker-stack.yml sre-app
docker stack services sre-app
docker stack ps sre-app
```

Capacity variant:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.capacity.yml sre-app
docker stack services sre-app
```

Placeholder:

```text
[Screenshot or terminal output: Docker Swarm services and capacity variant]
```

### 14.9 Ansible Evidence

How to capture:

```bash
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/site.yml
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/k8s.yml
ansible-playbook -i ansible/inventory.ini ansible/k8s.yml
```

Placeholder:

```text
[Screenshot or terminal output: Ansible syntax checks and Kubernetes apply]
```

### 14.10 Terraform Evidence

How to capture:

```bash
cd infra/terraform
terraform init
terraform plan
terraform output droplet_public_ip
```

Placeholder:

```text
[Screenshot or terminal output: Terraform plan/output]
```

## 15. Conclusion

This project implements a complete SRE demonstration for a distributed microservices platform. It combines service design, deployment automation, infrastructure provisioning, observability, incident response, and capacity planning into a single reproducible repository suitable for end-term evaluation.

Final Git link: <https://github.com/nurzhqn0/sre-app.git>
