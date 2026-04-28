# Final Submission Report

## Project Title

Design and Deployment of a Containerized Microservices System with Terraform-Based Infrastructure Provisioning and Incident Response Simulation

## Executive Summary

This project implements a containerized microservices platform using FastAPI, React, Nginx, PostgreSQL, Prometheus, Grafana, Docker Compose, Docker Stack, and Terraform. The system demonstrates service isolation, HTTP-based inter-service communication, observability, infrastructure reproducibility, and structured incident response. A simulated production incident was introduced in `order-service` by breaking its database configuration and then resolving it through a standard detect-analyze-mitigate-restore workflow.

## Architecture Summary

- Frontend: React application served by Nginx
- Gateway: Nginx reverse proxy with route-based request forwarding
- Backend services:
  - authentication service
  - user service
  - product service
  - order service
  - chat service
- Database: PostgreSQL
- Monitoring: Prometheus and Grafana
- IaC: Terraform for DigitalOcean Droplet and firewall provisioning

## Requirement Alignment

### Functional Requirements

- Web-based interface: implemented in the React frontend
- Authentication and authorization: implemented with registration, login, JWT-based protected routes
- Product retrieval: implemented through `product-service`
- Transactional operations: implemented through `order-service`
- Backend service communication: implemented over HTTP and WebSocket
- Metrics exposure: implemented through `/metrics` endpoints in each service
- Failure detection and logging: implemented through health endpoints, Prometheus targets, Grafana dashboards, and container logs

### Non-Functional Requirements

- Scalability and modularity: services are separated by responsibility
- Fault isolation: order-service incident does not take down unrelated services
- Observability: Prometheus scrape targets and Grafana dashboard are configured
- Automated deployment: Terraform and Docker manifests are provided
- Cross-environment portability: services run in containers
- Reproducibility: infrastructure and application configuration are declared in code

## Infrastructure As Code Summary

Terraform files included:
- `infra/terraform/main.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf`
- `infra/terraform/terraform.tfvars.example`

Provisioned resources:
- DigitalOcean Droplet
- DigitalOcean firewall with inbound rules for ports `22`, `80`, `3000`, and `9090`

## Incident Response Summary

- Incident type: configuration failure in `order-service`
- Trigger: invalid PostgreSQL hostname in `DATABASE_URL`
- Impact: users cannot create or list orders
- Detection methods:
  - frontend failure symptoms
  - Prometheus target degradation
  - Grafana availability degradation
  - container log analysis
- Resolution: restore healthy configuration and restart `order-service`

## Evidence Checklist

Insert screenshots into the final PDF for:
- running Docker Compose containers
- Docker Stack service list
- frontend application
- Prometheus targets
- Grafana dashboard
- system before incident
- order-service failure during incident
- order-service logs
- system after recovery
- Terraform init, plan, apply, and public IP output

## Linked Deliverables

- README and setup instructions: `README.md`
- Deployment guide: `docs/deployment-guide.md`
- Security guide: `docs/security-guidelines.md`
- Incident report: `docs/incident-report.md`
- Postmortem: `docs/postmortem.md`
- Terraform explanation: `docs/assignment-5-terraform.md`

## Finalization Note

If Docker or cloud credentials are unavailable at report-generation time, the code and report package can still be finalized, but screenshots and live command evidence must be captured later from a working runtime environment before submission.
