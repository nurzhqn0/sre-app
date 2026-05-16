# SRE Project Defence Preparation Guide

## 1. Opening Summary

Use this as your opening:

> My project demonstrates a complete Site Reliability Engineering lifecycle for a distributed microservices system. It includes six backend services, a React/Nginx frontend, PostgreSQL, Docker Compose, Docker Swarm, Kubernetes manifests, Terraform infrastructure provisioning, Ansible automation, Prometheus monitoring, Grafana dashboards, alerting, incident simulation, postmortem analysis, and capacity planning.

GitHub repository:

<https://github.com/nurzhqn0/sre-app.git>

## 2. Project Architecture

The system is a microservices-based e-commerce reliability demo.

The frontend communicates through Nginx with six backend services:

| Service | Purpose |
| --- | --- |
| `auth-service` | User registration, login, and JWT authentication |
| `user-service` | User profile and user data |
| `product-service` | Product catalog |
| `order-service` | Order creation and order listing |
| `payment-service` | Simulated payment authorization |
| `chat-service` | WebSocket operations chat |

Supporting components:

| Component | Purpose |
| --- | --- |
| `frontend` | React UI served by Nginx |
| `postgres` | Shared relational database |
| `prometheus` | Metrics collection and alert evaluation |
| `grafana` | Dashboard visualization |
| `cadvisor` | Container CPU, memory, and restart metrics |

Architecture flow:

```text
User
  |
Frontend / Nginx
  |
  +--> auth-service
  +--> user-service
  +--> product-service
  +--> order-service
  +--> payment-service
  +--> chat-service
  |
PostgreSQL

Prometheus --> Grafana
Terraform --> VM provisioning
Ansible --> setup and deployment automation
Docker Swarm + Kubernetes --> orchestration
```

## 3. SRE Concepts To Explain

### SLI

An SLI, or Service Level Indicator, is a measurable reliability metric.

Examples in this project:

- availability
- latency
- error rate
- request success rate

### SLO

An SLO, or Service Level Objective, is the target value for an SLI.

Project SLOs:

| SLI | SLO |
| --- | --- |
| Availability | `>= 99%` |
| Latency | p95 `<= 200 ms` |
| Error rate | `<= 1%` |
| Success rate | `>= 99%` |

### SLA

An SLA is a formal reliability agreement with users or customers. This project defines SLOs, but not a real commercial SLA.

### Error Budget

An error budget is the allowed amount of unreliability. For example, if availability target is `99%`, then the system has a `1%` error budget.

### Observability

Observability means understanding system health using metrics, logs, dashboards, and alerts.

In this project:

- Prometheus collects metrics.
- Grafana shows dashboards.
- Docker logs help diagnose failures.
- Alert rules detect unhealthy services.

## 4. Monitoring and Alerting

Each backend service exposes:

```text
/health
/metrics
```

Prometheus scrapes metrics from all backend services.

Important metrics:

- `service_http_requests_total`
- `service_http_request_duration_seconds`
- `service_health_status`
- container CPU usage from cAdvisor
- container memory usage from cAdvisor
- container restart events

Alert examples:

- service target down
- service health check failing
- high 5xx error rate
- high p95 latency
- high order-service CPU usage
- container restart detected

Defence answer:

> Monitoring is implemented with Prometheus and Grafana. Prometheus collects service metrics from `/metrics`, evaluates alert rules, and Grafana visualizes service health, latency, errors, CPU, memory, and restarts.

## 5. Incident Simulation

The simulated incident breaks `order-service` by giving it an invalid PostgreSQL hostname.

Incident command:

```bash
docker compose -f docker-compose.yml -f docker-compose.incident.yml up -d order-service
```

Expected impact:

- order creation fails
- order listing fails
- `order-service` health check fails
- Prometheus detects degraded health
- Grafana shows service degradation
- alerts fire

Recovery command:

```bash
docker compose up -d order-service
```

Root cause:

> The root cause was an invalid `DATABASE_URL` in the `order-service` configuration.

Prevention:

- validate configuration before deployment
- use health checks
- use Prometheus alerts
- review logs during incident response
- document the incident in a postmortem

## 6. Docker Compose, Swarm, and Kubernetes

### Docker Compose

Docker Compose is used for local deployment and testing.

Command:

```bash
docker compose up -d --build
```

Why it is used:

- simple local orchestration
- easy service startup
- useful for demos and validation

### Docker Swarm

Docker Swarm is used to demonstrate clustering, replicas, overlay networking, and stack deployment.

Command:

```bash
docker stack deploy -c docker-stack.yml sre-app
```

Capacity deployment:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.capacity.yml sre-app
```

### Kubernetes

Kubernetes is used to demonstrate declarative orchestration.

Command:

```bash
kubectl apply -f k8s/
```

Kubernetes objects used:

- Namespace
- Secret
- ConfigMap
- Deployment
- Service
- PersistentVolumeClaim
- DaemonSet

Comparison:

| Feature | Docker Swarm | Kubernetes |
| --- | --- | --- |
| Complexity | Easier | More complex |
| Scaling | Supported | Advanced |
| Self-healing | Basic | Strong |
| Configuration | Stack files | Declarative manifests |
| Best use | Simple clusters | Production-grade orchestration |

## 7. Terraform

Terraform is used for infrastructure provisioning.

In this project, Terraform provisions:

- DigitalOcean droplet
- firewall rules
- SSH and HTTP access configuration

Files:

- `infra/terraform/main.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf`
- `infra/terraform/terraform.tfvars.example`

Command sequence:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
terraform output droplet_public_ip
```

Defence answer:

> Terraform makes infrastructure reproducible and version-controlled. Instead of manually creating servers and firewall rules, the infrastructure is declared as code.

## 8. Ansible

Ansible is used for configuration management and deployment automation.

Files:

- `ansible/inventory.ini`
- `ansible/site.yml`
- `ansible/k8s.yml`

Ansible automates:

- Docker dependency installation on Debian hosts
- Docker service startup
- Compose configuration validation
- application deployment
- service status checks
- Kubernetes manifest application when `kubectl` is available

Commands:

```bash
ansible-playbook -i ansible/inventory.ini ansible/site.yml
ansible-playbook -i ansible/inventory.ini ansible/k8s.yml
```

Defence answer:

> Ansible reduces manual deployment mistakes by automating repeated setup and deployment tasks.

## 9. Capacity Planning

Capacity planning identifies bottlenecks and scaling strategies.

Most resource-sensitive services:

- `order-service`
- `payment-service`
- `postgres`

Why:

- order creation writes to the database
- payment authorization writes to the database
- PostgreSQL is shared by all backend services

Scaling strategies:

- horizontally scale `order-service`
- horizontally scale `payment-service`
- increase CPU/RAM for PostgreSQL if database load is high
- monitor CPU, memory, latency, error rate, and restarts
- use load testing to identify bottlenecks

Capacity deployment command:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.capacity.yml sre-app
```

Defence answer:

> Capacity planning in this project focuses on order and payment workflows because they are write-heavy and depend on PostgreSQL. The scaling strategy is to increase service replicas first, then optimize or resize the database if PostgreSQL becomes the bottleneck.

## 10. Demo Flow

Recommended defence demo order:

1. Show the GitHub repository.
2. Open `README.md`.
3. Open `docs/end-term-project.md`.
4. Explain the architecture diagram.
5. Show the six backend services.
6. Open `docker-compose.yml`.
7. Show `payment-service`.
8. Show `monitoring/prometheus/prometheus.yml`.
9. Show `monitoring/prometheus/alerts.yml`.
10. Show Grafana dashboard configuration.
11. Show `docker-compose.incident.yml`.
12. Explain the incident and recovery process.
13. Show `k8s/` manifests.
14. Show `ansible/` playbooks.
15. Show `infra/terraform/` files.

If Docker is running:

```bash
docker compose up -d --build
```

Open:

- frontend: `http://localhost`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

## 11. Common Defence Questions and Answers

### Why did you use microservices?

To demonstrate distributed system reliability, independent service deployment, health checks, monitoring, and fault isolation.

### Why did you use both Docker Swarm and Kubernetes?

To compare orchestration approaches. Docker Swarm is simpler and fast to deploy, while Kubernetes is more powerful and widely used for production orchestration.

### What happens when one service fails?

The failure is isolated to the affected workflow. For example, when `order-service` fails, authentication, products, payments, chat, and the frontend can still remain available.

### How do you detect incidents?

Incidents are detected using service health checks, Prometheus metrics, Grafana dashboards, and alert rules.

### What was the simulated incident?

The `order-service` was configured with an invalid PostgreSQL hostname, causing database connection failure.

### What was the root cause?

The root cause was an invalid `DATABASE_URL` value.

### How did you recover?

I restored the correct configuration and restarted `order-service`.

### Why did you add `payment-service`?

The assignment requires at least six microservices. `payment-service` adds a realistic independent business workflow connected to orders.

### What does Prometheus do?

Prometheus collects metrics from services and evaluates alert rules.

### What does Grafana do?

Grafana visualizes metrics using dashboards.

### What does Terraform do?

Terraform provisions infrastructure such as VMs and firewall rules.

### What does Ansible do?

Ansible automates system setup, validation, deployment, and Kubernetes manifest application.

### What are your main SLIs?

The main SLIs are availability, latency, error rate, and request success rate.

### What is the most important service?

`order-service` is critical because it represents the main business workflow. `payment-service` is also important because it completes the order lifecycle.

## 12. Short Final Speech

Use this closing statement:

> This project demonstrates how SRE practices improve reliability in a distributed system. The implementation includes monitoring, alerting, incident response, automation, infrastructure as code, orchestration, and capacity planning. The main value of the project is that reliability is not only described in documentation, but implemented through working services, deployment files, monitoring configuration, and operational runbooks.

## 13. Last-Minute Checklist

Before defence, confirm:

- `README.md` explains the project.
- `docs/end-term-project.md` is complete.
- `docs/defence-guide.md` is ready.
- GitHub link is available.
- Six backend services are visible.
- `payment-service` is implemented.
- Docker Compose file includes all services.
- Kubernetes manifests exist.
- Ansible playbooks exist.
- Terraform files exist.
- Prometheus and Grafana files exist.
- Incident report and postmortem exist.

Useful validation commands:

```bash
python3 scripts/validate_compose_config.py -f docker-compose.yml
cd frontend
npm run build
cd ..
docker compose config --quiet
```
