# Incident Response Simulation Report

## Incident Summary

- **Service affected:** `order-service`
- **Scenario:** invalid database hostname injected into `order-service`
- **Severity:** Sev-2
- **Customer impact:** users cannot create or retrieve orders while other services remain online

## Timeline Of Events

| Time | Event |
| --- | --- |
| T+00 min | Incident introduced by deploying the `docker-compose.incident.yml` override for `order-service`. |
| T+01 min | Frontend order creation requests begin failing. |
| T+02 min | `order-service` health endpoint stops returning healthy responses. |
| T+03 min | Prometheus health metric `service_health_status{service="order-service"}` drops from `1` to `0`. |
| T+04 min | Grafana dashboard shows order-service health degradation. |
| T+06 min | Container logs confirm database hostname resolution or connection failure. |
| T+08 min | Faulty configuration removed and `order-service` restarted with healthy settings. |
| T+10 min | Prometheus health metric returns to `1`, Grafana dashboard recovers, and order creation succeeds again. |

## Detection

The incident is introduced by applying the Compose override file:

```bash
docker compose -f docker-compose.yml -f docker-compose.incident.yml up -d order-service
```

Detection signals:
- frontend order creation fails
- `order-service` health endpoint fails
- Prometheus health metric for `order-service` becomes `0`
- Prometheus alert for `order-service` fires
- Grafana service health panel turns unhealthy

## Investigation

Run:

```bash
docker compose ps
docker compose logs order-service
curl -s 'http://localhost:9090/api/v1/query?query=service_health_status{service="order-service"}'
curl -s http://localhost:9090/api/v1/alerts
```

Expected finding:
- `order-service` cannot resolve or connect to the configured PostgreSQL hostname

## Mitigation

Restore the original configuration:

```bash
docker compose up -d order-service
```

Then verify:

```bash
curl -s http://localhost/api/orders/health
```

## Resolution Confirmation

Confirm the following after mitigation:
- order creation succeeds again from the UI
- `service_health_status{service="order-service"}` returns to `1`
- Prometheus alerts for `order-service` clear
- Grafana shows healthy order-service status
- logs no longer show database connection errors

## Impact Assessment

- Affected capability: order creation and order retrieval
- Unaffected capabilities: login, registration, product browsing, user listing, chat
- Scope: isolated to the `order-service`
- Duration: approximately 10 minutes in the simulated timeline

## Root Cause Analysis

The direct cause was an intentionally invalid PostgreSQL hostname in the `DATABASE_URL` used by `order-service`. The service could still start at the container level, but request handling and health validation failed once database access was required. Monitoring correctly reflected the failure because the health endpoint failed, the exported `service_health_status` metric dropped to `0`, and the related alert rules fired.

## Required Screenshot Inserts

Insert screenshots for:
- application before incident
- failed order action during incident
- `docker compose logs order-service`
- Prometheus graph or alerts page showing `service_health_status{service="order-service"} = 0`
- Grafana dashboard showing degraded service health
- system after recovery

Recommended filenames:
- `01-healthy-frontend.png`
- `02-incident-order-failure.png`
- `03-order-service-logs.png`
- `04-prometheus-targets-incident.png`
- `05-grafana-incident-dashboard.png`
- `06-recovery-frontend.png`
