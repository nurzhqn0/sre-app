# End-to-End SRE Implementation for a Multi-Orchestrated Microservices System

## 1. Abstract

This project implements Site Reliability Engineering practices across a distributed microservices platform. The system uses six independent FastAPI backend services, a React frontend served by Nginx, PostgreSQL, Docker Compose, Docker Swarm, Kubernetes, Terraform, Ansible, Prometheus, Grafana, and incident-response documentation.

The project demonstrates the full SRE lifecycle: service design, containerization, orchestration, infrastructure provisioning, configuration automation, SLIs/SLOs, monitoring, alerting, incident simulation, postmortem analysis, and capacity planning.

Git repository: <https://github.com/nurzhqn0/sre-app.git>

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

## 6. Infrastructure as Code

Terraform files in `infra/terraform/` provision a DigitalOcean droplet and firewall. The firewall exposes SSH and frontend HTTP while keeping monitoring private for SSH tunnel access.

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

Alert coverage includes:

- unhealthy service health metric
- down Prometheus scrape targets
- high 5xx rate
- high p95 latency
- high order-service CPU usage
- container restart detection

## 10. Incident Simulation and Postmortem

Incident scenario: `order-service` receives an invalid PostgreSQL hostname through an override file.

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

Optional full local demo:

```bash
docker compose up -d --build
```

Capture evidence:

- frontend product, order, payment, chat, and health views
- Prometheus targets with all backend services including `payment-service`
- Grafana dashboard showing service health and resource metrics
- order-service incident state
- recovery state after restoring the correct database configuration
- Swarm service list and capacity override
- Kubernetes pod and service list

## 14. Conclusion

This project implements a complete SRE demonstration for a distributed microservices platform. It combines service design, deployment automation, infrastructure provisioning, observability, incident response, and capacity planning into a single reproducible repository suitable for end-term evaluation.

Final Git link: <https://github.com/nurzhqn0/sre-app.git>
