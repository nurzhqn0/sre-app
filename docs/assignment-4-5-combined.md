# Assignment 4-5 Combined Report

## Title

Design and Deployment of a Containerized Microservices System with Terraform-Based Infrastructure Provisioning and Incident Response Simulation

## Executive Summary

This project combines Infrastructure as Code and Site Reliability Engineering practices in one containerized microservices platform. The system uses FastAPI backend services, a React frontend served by Nginx, PostgreSQL, Prometheus, Grafana, Docker Compose, Docker Stack, and Terraform on DigitalOcean. Assignment 5 covers infrastructure provisioning and deployment, while Assignment 4 covers incident simulation, structured response, and postmortem analysis.

## System Overview

### Architecture

- Frontend layer: React application served by Nginx
- Reverse proxy: Nginx request routing for frontend and backend APIs
- Backend microservices:
  - authentication service
  - user service
  - product service
  - order service
  - chat service
- Database layer: PostgreSQL
- Monitoring layer:
  - Prometheus for metrics collection
  - Grafana for dashboard visualization

### Functional Coverage

- user authentication and authorization
- product retrieval and display
- order creation and order listing
- chat communication
- service-to-service HTTP communication
- metrics exposure and health validation
- service failure detection through monitoring and logs

### Non-Functional Coverage

- modular service separation
- fault isolation between services
- reproducible infrastructure provisioning
- containerized deployment across environments
- observability through metrics and dashboards

## Assignment 5: Terraform Infrastructure Provisioning

### Objective

Provision the deployment environment in a declarative and reproducible way using Terraform.

### Terraform Scope

Terraform provisions:

- one `digitalocean_droplet`
- one `digitalocean_firewall`

The firewall allows:

- `22` for SSH
- `80` for HTTP frontend access

Monitoring exposure model:

- Grafana and Prometheus are accessed through SSH port forwarding
- monitoring ports are not opened publicly in the Terraform firewall

### Terraform Files

- `infra/terraform/main.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf`
- `infra/terraform/terraform.tfvars.example`

### Version Targets

- Terraform CLI `1.14.x`
- DigitalOcean provider `2.69.x`

### Commands

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
terraform output droplet_public_ip
```

### Configuration Notes

- `main.tf` defines the provider, Droplet, and firewall
- `variables.tf` defines reusable input variables
- `outputs.tf` exposes the public IP and Droplet name
- `terraform.tfvars.example` provides a safe template for local secret values
- the real `terraform.tfvars` should remain local and ignored

### Deployment Workflow After Terraform

1. Provision the Droplet with Terraform.
2. SSH into the new server.
3. Install Docker and Docker Compose or Docker Swarm tooling.
4. Clone the repository.
5. Create a local `.env` from `.env.example`.
6. Deploy the platform with Docker Compose or Docker Stack.
7. If the server runs Docker Compose, create SSH tunnels for monitoring:

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 root@YOUR_PUBLIC_IP
```

8. If the server runs Docker Stack, create SSH tunnels for monitoring:

```bash
ssh -L 3001:127.0.0.1:3001 -L 9091:127.0.0.1:9091 root@YOUR_PUBLIC_IP
```

### Terraform Evidence To Include

Add screenshots of:

- `terraform init`
- `terraform plan`
- `terraform apply`
- `terraform output droplet_public_ip`
- the application reachable by public IP

Recommended capture steps:

1. Run `terraform init` and capture the successful initialization output.
2. Run `terraform plan` and capture the planned Droplet and firewall resources.
3. Run `terraform apply` and capture the successful creation summary.
4. Run `terraform output droplet_public_ip` and capture the returned public IP.
5. Open the deployed application by public IP and capture the browser page as proof of successful provisioning.

Suggested filenames:

- `01-terraform-init.png`
- `02-terraform-plan.png`
- `03-terraform-apply.png`
- `04-terraform-public-ip.png`
- `05-public-ip-application.png`

## Assignment 4: Incident Response Simulation

### Objective

Simulate a realistic service outage and evaluate the incident response process.

### Incident Scenario

The incident is introduced in `order-service` by using an invalid PostgreSQL hostname in `DATABASE_URL`. This causes order creation and order retrieval to fail while other services remain functional.

### Incident Summary

- affected service: `order-service`
- severity: Sev-2
- affected capability: order creation and order retrieval
- unaffected capability: authentication, products, chat, frontend availability

### Detection

The incident is introduced with:

```bash
docker compose -f docker-compose.yml -f docker-compose.incident.yml up -d order-service
```

Detection signals:

- failed order operations in the frontend
- `order-service` health endpoint failure
- Prometheus health metric `service_health_status{service="order-service"}` changing from `1` to `0`
- Prometheus alert for `order-service` firing
- Grafana service health panel showing service degradation

### Timeline Of Events

| Time | Event |
| --- | --- |
| T+00 min | Fault introduced into `order-service` database configuration |
| T+01 min | Frontend order operations begin failing |
| T+02 min | `order-service` health endpoint becomes unhealthy |
| T+03 min | Prometheus health metric for `order-service` changes from `1` to `0` |
| T+04 min | Grafana dashboard shows service health failure |
| T+06 min | Logs confirm database hostname resolution or connection failure |
| T+08 min | Healthy configuration restored and service restarted |
| T+10 min | Service recovery confirmed in UI and monitoring |

### Investigation

Commands used during diagnosis:

```bash
docker compose ps
docker compose logs order-service
curl -s 'http://localhost:9090/api/v1/query?query=service_health_status{service="order-service"}'
curl -s http://localhost:9090/api/v1/alerts
```

Root finding:

- `order-service` could not resolve or connect to PostgreSQL because of an invalid hostname in its connection string

### Mitigation

Restore the healthy service configuration:

```bash
docker compose up -d order-service
```

Then verify:

```bash
curl -s http://localhost/api/orders/health
```

### Resolution Confirmation

Recovery is confirmed when:

- order creation succeeds again
- `order-service` health endpoint returns `ok`
- `service_health_status{service="order-service"}` returns `1`
- Prometheus clears the unhealthy alert
- Grafana dashboard shows normal service health
- logs no longer show database connection errors

### Incident Evidence To Include

Capture the following screenshots in this order:

1. Healthy platform before fault injection.
2. Failed order creation or failed order retrieval after the incident is introduced.
3. Container status during the incident using `docker compose ps`.
4. `order-service` logs showing the database connection or hostname failure.
5. Prometheus graph or alerts page showing `service_health_status{service="order-service"} = 0`.
6. Grafana dashboard showing order-service health degradation.
7. Healthy platform after restoring the correct configuration.

Suggested filenames:

- `06-compose-healthy.png`
- `07-incident-order-failure.png`
- `08-compose-incident-status.png`
- `09-order-service-logs.png`
- `10-prometheus-incident.png`
- `11-grafana-incident.png`
- `12-compose-recovery.png`

## Postmortem Analysis

### Incident Overview

The incident was caused by a deliberate misconfiguration in the `order-service` database connection. The system behaved as expected in terms of failure isolation because only order-related functionality was degraded.

### Customer Impact

- users could still authenticate
- users could still browse products
- users could still access chat
- users could not create or retrieve orders

### Root Cause Analysis

The root cause was an invalid `DATABASE_URL` for `order-service`. The service depends on PostgreSQL for both reads and writes. Once the hostname became invalid, health checks and order endpoints failed.

### Detection And Response Evaluation

- detection was effective because the outage was visible through frontend failures, logs, Prometheus targets, and Grafana panels
- response was effective because the fault was isolated and reversible by restoring the correct configuration

### Resolution Summary

1. Observed order failures in the frontend.
2. Confirmed service degradation in health checks and monitoring.
3. Reviewed container logs to identify the database configuration error.
4. Removed the faulty configuration and restarted `order-service`.
5. Validated normal behavior through UI, health endpoints, and monitoring.

### Lessons Learned

- health endpoints reduced time to confirmation
- monitoring made the degraded service visible quickly
- configuration validation should be added before deployment

### Action Items

1. Add configuration validation for service environment variables before deployment.
2. Add alert rules for `order-service` availability and error rate.
3. Add a synthetic transaction check for order creation.
4. Enforce configuration review before rollout.

## Deployment And Operations Notes

### Docker Compose

Docker Compose is used for the main local deployment path with:

- frontend
- backend services
- PostgreSQL
- Prometheus
- Grafana

### Docker Stack

Docker Stack is used to demonstrate Swarm orchestration of the same platform. Published ports may need to be adjusted if other Swarm services already use the defaults.

### Monitoring Validation

System health is validated through:

- service availability endpoints
- Prometheus metrics targets
- Grafana dashboard visualization

## Evidence Checklist

Add screenshots for the final PDF submission:

- running containers
- Docker Stack services and tasks
- frontend application
- Prometheus targets
- Grafana dashboard
- Terraform `init`, `plan`, `apply`, and public IP output
- system before the incident
- failed order workflow during the incident
- `order-service` logs during the incident
- system after service restoration

### How To Capture Each Screenshot

#### Running containers

Run:

```bash
docker compose ps
```

Capture the full terminal output showing all containers and their status.

#### Docker Stack services and tasks

Run:

```bash
docker stack services sre-app
docker stack ps sre-app
```

Capture one screenshot for services and one for task placement/status.

#### Frontend application

Open the frontend in the browser and capture:

- login/register page
- product list page
- order page
- chat page
- status/health page if visible

#### Prometheus targets

Open:

- local Compose path: `http://localhost:9090/graph`
- remote Compose path through SSH tunnel: `http://localhost:9090/graph`
- remote Swarm path through SSH tunnel: `http://localhost:9091/graph`

Use the query:

```promql
service_health_status{service="order-service"}
```

Capture the graph or table showing `1` before the incident and `0` during the incident. You can also capture the Alerts page if `OrderServiceHealthUnhealthy` is firing.

#### Grafana dashboard

Open:

- local Compose path: `http://localhost:3000`
- remote Compose path through SSH tunnel: `http://localhost:3000`
- remote Swarm path through SSH tunnel: `http://localhost:3001`

Capture the dashboard in healthy state and incident state, focusing on the order-service health panel.

#### Before and after incident

Before incident:

1. ensure the stack is healthy
2. capture frontend order workflow working
3. capture Prometheus health metric with value `1`
4. capture Grafana healthy order-service panel

After incident:

1. inject the `order-service` fault
2. capture failed behavior and degraded monitoring
3. restore service
4. capture recovered frontend and monitoring state

### Screenshot Placement In The Final PDF

Use this sequence in the final PDF:

1. Terraform screenshots
2. Docker Compose healthy deployment screenshots
3. Docker Stack screenshots
4. Prometheus and Grafana healthy-state screenshots
5. Incident screenshots during failure
6. Recovery screenshots

## Conclusion

This combined Assignment 4-5 submission demonstrates the integration of containerization, infrastructure automation, observability, and incident management. Terraform provisions the deployment environment, Docker orchestrates the platform, Prometheus and Grafana provide visibility, and the incident simulation validates operational response and postmortem practice.
