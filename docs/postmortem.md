# Postmortem Analysis

## Incident Overview

An intentional configuration fault was introduced into `order-service` by changing its PostgreSQL hostname. This caused order-related API failures while leaving authentication, products, user management, and chat functional.

## Customer Impact

- users could browse products and authenticate
- users could not create new orders or view existing orders
- frontend remained reachable but order workflows were degraded

## Root Cause Analysis

The root cause was an invalid `DATABASE_URL` for `order-service`. The service depends on PostgreSQL for both reads and writes. Once the hostname became invalid, health checks and order endpoints failed.

## Detection And Response Evaluation

- Detection was successful through a mix of UI symptoms, Prometheus target health, Grafana dashboard degradation, and container logs.
- Response was effective because the issue was isolated to one service and could be reversed by restoring environment configuration and restarting the service.

## Resolution Summary

1. Observed order failures in the frontend.
2. Confirmed `order-service` health failure and Prometheus degradation.
3. Inspected container logs to identify the broken database hostname.
4. Removed the faulty override and restarted `order-service`.
5. Validated normal behavior through UI, health checks, and metrics.

## Lessons Learned

- health endpoints made failure confirmation faster
- shared metrics improved visibility of service state
- configuration changes need stronger validation before rollout

## Action Items

1. Add automated config validation for service environment variables before deployment.
2. Add explicit alert rules for `order-service` availability dropping below `1`.
3. Add a synthetic check that exercises order creation end-to-end.
4. Store deployment configuration in version-controlled templates with review.
