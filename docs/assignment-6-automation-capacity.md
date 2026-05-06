# Assignment 6: Automation and Capacity Planning in SRE

## 1. Title

Automation and Capacity Planning in a Containerized Microservices System Following Incident Response and Infrastructure Provisioning.

## 2. Objective

This assignment extends the existing microservices platform from Assignment 4 and Assignment 5 with operational automation, monitoring-based alerting, capacity analysis, and scaling guidance. The system remains a Dockerized microservices application with a React/Nginx frontend, FastAPI backend services, PostgreSQL, Prometheus, Grafana, and Terraform-managed infrastructure.

The main reliability concern carried forward from Assignment 4 is the order-service failure caused by an invalid database configuration. Assignment 6 addresses that failure mode with pre-deployment validation, health checks, self-healing container policies, alerting, log inspection, and capacity planning for higher order-service load.

## 3. Automation Mechanisms

### Automated deployment

Deployment is standardized through `docker-compose.yml` for local/container deployment and `docker-stack.yml` for Swarm deployment. The Terraform configuration in `infra/terraform` provisions the target DigitalOcean Droplet and firewall used by the application.

Key deployment automation:

- `docker compose up -d --build` starts the complete platform consistently.
- `docker stack deploy -c docker-stack.yml sre-app` deploys the Swarm baseline.
- `.env.example` defines the supported environment variables.
- `scripts/validate_compose_config.py` runs before deployment to catch invalid service configuration.

Validation command:

```bash
python3 scripts/validate_compose_config.py -f docker-compose.yml
```

Incident validation command:

```bash
python3 scripts/validate_compose_config.py -f docker-compose.yml -f docker-compose.incident.yml
```

The incident validation is expected to fail because the override changes the order-service database hostname to `postgres-broken`.

### Health checks and self-healing

Each application service exposes `/health` and `/metrics`. Docker health checks verify service availability, and `restart: unless-stopped` keeps containers running after unexpected exits in the Compose environment.

Covered services:

- `auth-service`
- `user-service`
- `product-service`
- `order-service`
- `chat-service`
- `frontend`
- `postgres`

The order-service health check validates database access, which directly addresses the Assignment 4 incident where a bad `DATABASE_URL` caused order functionality to fail.

### Monitoring and alerting

Prometheus scrapes service metrics and cAdvisor container metrics. The Prometheus configuration now includes:

- service health metrics from `/metrics`
- request count and status metrics
- request latency histograms
- cAdvisor CPU, memory, and container start-time metrics
- alert rules from `monitoring/prometheus/alerts.yml`

cAdvisor is pinned to `ghcr.io/google/cadvisor:v0.56.2`, matching the current GitHub release listing checked on 2026-05-06.

Implemented alert categories:

- service health failure
- service scrape target down
- order-service health failure
- order-service target down
- elevated 5xx rate
- high p95 latency
- high order-service CPU usage
- detected container restart

Grafana dashboard panels support capacity and reliability review:

- order-service health
- order-service 5xx rate
- order-service CPU usage
- order-service restart events
- per-service request volume
- per-service p95 latency
- per-service 5xx rate
- per-service CPU usage
- per-service memory usage
- service health table
- container restart signals

### Log-based troubleshooting

The log inspection helper scans recent Docker Compose logs for common incident patterns:

```bash
python3 scripts/inspect_logs.py --tail 300
```

Patterns include:

- database connection failures
- DNS or endpoint resolution failures
- HTTP 5xx symptoms
- restart-loop and health-check messages

This helps shorten diagnosis time when order-service or database connectivity fails.

## 4. Capacity Planning

### Metrics collected

Capacity planning uses both application and container metrics:

| Metric | Source | Purpose |
| --- | --- | --- |
| Request rate | `service_http_requests_total` | Identify load per service |
| Error rate | `service_http_requests_total{status=~"5.."}` | Detect overload or dependency failures |
| p95 latency | `service_http_request_duration_seconds_bucket` | Measure user-facing response delay |
| CPU usage | `container_cpu_usage_seconds_total` | Identify CPU saturation |
| Memory usage | `container_memory_working_set_bytes` | Identify memory pressure |
| Restart signals | `container_start_time_seconds` | Detect recovery events and instability |

### Load simulation

The load test script exercises the realistic order flow:

1. Register a test user or log in if the user already exists.
2. Fetch a seeded product from product-service.
3. Create concurrent orders through the frontend/Nginx API path.
4. Print request count, success count, error count, error rate, RPS, p95, p99, and HTTP status counts.

Command:

```bash
python3 scripts/load_test.py --base-url http://localhost --users 20 --requests 200
```

Example result format:

```json
{
  "base_url": "http://localhost",
  "concurrency": 20,
  "error_count": 0,
  "error_rate": 0.0,
  "p95_seconds": 0.0,
  "p99_seconds": 0.0,
  "requests": 200,
  "rps": 0.0,
  "status_counts": {
    "201": 200
  },
  "success_count": 200,
  "username": "loadtest_..."
}
```

Replace the zero values above with observed values after running the test in the target environment.

### Expected observations under increased load

The order-service is the most resource-sensitive service because each order creation performs:

- request authentication
- product-service lookup
- order total calculation
- PostgreSQL insert
- response serialization

Under higher concurrency, the expected bottlenecks are:

- increased order-service CPU usage
- higher p95 and p99 latency
- increased 5xx rate if dependencies become unavailable or saturated
- PostgreSQL connection pressure if many concurrent inserts occur
- product-service dependency latency affecting order creation

### Capacity analysis

Capacity should be evaluated from each load test run using:

- maximum sustainable RPS before p95 exceeds 1 second
- error rate staying below 1 percent during steady-state load
- order-service CPU staying below 80 percent for sustained periods
- memory staying below configured container limits
- zero unexpected restart events during the test window

The first scaling target is order-service because it combines dependency calls and write-heavy order creation. If order-service CPU reaches the alert threshold before PostgreSQL does, horizontal scaling is the primary response. If PostgreSQL CPU, memory, or connection usage rises first, database tuning becomes the priority.

## 5. Scaling Strategy

### Horizontal scaling

The Swarm capacity override scales order-service to two replicas:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.capacity.yml sre-app
```

The override also documents resource reservations and limits for order-service, product-service, and PostgreSQL.

Validation commands:

```bash
docker stack services sre-app
docker stack ps sre-app
python3 scripts/load_test.py --base-url http://localhost:8080 --users 20 --requests 200
```

Expected outcome:

- order-service has two replicas
- request handling is distributed by Swarm networking
- p95 latency improves or stays stable under the same load
- CPU pressure per order-service replica decreases

### Vertical scaling

Terraform already exposes `droplet_size` as a configurable variable. If the full platform is resource-constrained, increase this value in `infra/terraform/terraform.tfvars` and apply the Terraform change.

Example:

```hcl
droplet_size = "s-2vcpu-4gb"
```

Vertical scaling is appropriate when all services compete for host CPU or memory, or when PostgreSQL needs more local resources.

### Database optimization

If load testing shows PostgreSQL as the bottleneck, prioritize:

- connection pooling
- query/index review
- PostgreSQL resource tuning
- moving PostgreSQL to managed database infrastructure for production-like deployments

## 6. Evidence Checklist

Capture the following screenshots or terminal outputs for final submission:

- `docker compose config --quiet`
- successful `python3 scripts/validate_compose_config.py -f docker-compose.yml`
- failed validation against `docker-compose.incident.yml`
- `docker compose ps` showing healthy containers
- frontend order creation under normal load
- Prometheus targets including `cadvisor`
- Prometheus alerts page showing loaded rules
- Grafana dashboard with service health, latency, error rate, CPU, memory, and restart panels
- load-test terminal output for baseline
- incident overlay with order-service unhealthy
- `scripts/inspect_logs.py` output identifying the incident pattern
- restored healthy service state
- Swarm capacity deployment showing two order-service replicas
- load-test terminal output after scaling

### Screenshot and Evidence Placeholders

Use the spaces below to insert screenshots or terminal-output captures before final submission.

#### Figure 1. Compose configuration validation

<div style="border: 1px solid #999; min-height: 260px; padding: 12px; margin: 12px 0;">
Paste screenshot or terminal output for `docker compose config --quiet` and successful `scripts/validate_compose_config.py` here.
</div>

#### Figure 2. Incident configuration validation failure

<div style="border: 1px solid #999; min-height: 260px; padding: 12px; margin: 12px 0;">
Paste screenshot or terminal output showing validation failure for `docker-compose.incident.yml` here.
</div>

#### Figure 3. Healthy Docker Compose services

<div style="border: 1px solid #999; min-height: 260px; padding: 12px; margin: 12px 0;">
Paste screenshot of `docker compose ps` showing healthy containers here.
</div>

#### Figure 4. Frontend order creation under normal load

<div style="border: 1px solid #999; min-height: 320px; padding: 12px; margin: 12px 0;">
Paste screenshot of the frontend order workflow here.
</div>

#### Figure 5. Prometheus targets and alert rules

<div style="border: 1px solid #999; min-height: 320px; padding: 12px; margin: 12px 0;">
Paste screenshots of Prometheus targets, including `cadvisor`, and the alerts page here.
</div>

#### Figure 6. Grafana capacity dashboard

<div style="border: 1px solid #999; min-height: 360px; padding: 12px; margin: 12px 0;">
Paste screenshot of Grafana service health, latency, error rate, CPU, memory, and restart panels here.
</div>

#### Figure 7. Baseline load test output

<div style="border: 1px solid #999; min-height: 260px; padding: 12px; margin: 12px 0;">
Paste terminal output from `scripts/load_test.py` before scaling here.
</div>

#### Figure 8. Incident detection and recovery

<div style="border: 1px solid #999; min-height: 320px; padding: 12px; margin: 12px 0;">
Paste screenshots or terminal output showing the order-service incident, log inspection result, and restored healthy state here.
</div>

#### Figure 9. Swarm capacity scaling evidence

<div style="border: 1px solid #999; min-height: 320px; padding: 12px; margin: 12px 0;">
Paste screenshot or terminal output showing two order-service replicas and post-scaling load-test output here.
</div>

## 7. Conclusion

The updated system improves operational reliability by combining pre-deployment validation, health checks, restart policies, metrics, alerting, log inspection, and documented capacity testing. These changes directly reduce the risk of repeating the Assignment 4 misconfiguration incident and provide a practical process for measuring and scaling the order-service path under increased demand.
