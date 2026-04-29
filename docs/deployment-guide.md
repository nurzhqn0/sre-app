# Deployment Guide

## Local Docker Compose Deployment

1. Confirm Docker Engine and Docker Compose are installed.
2. Optionally create a local `.env` from `.env.example`.
3. Build and start the platform:

```bash
docker compose up -d --build
```

Current infrastructure and monitoring version targets:
- Terraform CLI `1.14.x`
- DigitalOcean provider `2.69.x`
- Grafana `13.0.1`
- Prometheus `3.11.2`

4. Verify containers:

```bash
docker compose ps
```

5. Verify endpoints:
   - Frontend: `http://localhost`
   - Grafana: `http://localhost:3000`
   - Prometheus: `http://localhost:9090`

Note:
- Grafana and Prometheus are bound to `127.0.0.1`
- they are reachable locally on the machine running Docker Compose
- they are not exposed to other hosts through the network interface

## Service Health Validation

Run these checks after the stack is healthy:

```bash
curl -s http://localhost/api/products/health
curl -s http://localhost/api/orders/health
curl -s http://localhost/api/auth/health
curl -s http://localhost/api/users/health
curl -s http://localhost/api/chat/health
```

Capture screenshots of:
- `docker compose ps`
- Frontend pages
- Prometheus targets
- Grafana dashboard

## Docker Stack Deployment

Use Docker Stack when you need to demonstrate Swarm orchestration for the full platform.

### Prerequisites

1. Docker Engine installed on the host.
2. Swarm mode enabled:

```bash
docker swarm init
```

3. Build local images for stack deployment:

```bash
./scripts/build-stack-images.sh
```

### Deploy

```bash
docker stack deploy -c docker-stack.yml sre-app
```

Default Swarm published ports are:

- `8080` for frontend
- `3001` for Grafana
- `9091` for Prometheus

For remote server deployments:
- keep frontend public only if needed
- keep Grafana and Prometheus private behind the Terraform firewall
- access monitoring through SSH port forwarding instead of opening those ports in the browser directly

If these are also occupied, deploy with alternate published ports:

```bash
STACK_HTTP_PORT=8081 STACK_GRAFANA_PORT=3002 STACK_PROMETHEUS_PORT=9092 docker stack deploy -c docker-stack.yml sre-app
```

### Verify

```bash
docker stack services sre-app
docker stack ps sre-app
docker service ls
```

Expected published ports by default:
- `8080` for frontend
- `3001` for Grafana
- `9091` for Prometheus

Alternative example when there is a port conflict:
- `8081` for frontend
- `3002` for Grafana
- `9092` for Prometheus

Recommended monitoring access on a remote Swarm node:

```bash
ssh -L 3001:127.0.0.1:3001 -L 9091:127.0.0.1:9091 root@PUBLIC_IP
```

Then open locally:
- `http://localhost:3001`
- `http://localhost:9091`

### Remove

```bash
docker stack rm sre-app
```

### Incident Simulation In Swarm

Inject the order-service database fault:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.incident.yml sre-app
```

Roll back to the healthy configuration:

```bash
docker stack deploy -c docker-stack.yml sre-app
```

Capture screenshots of:
- `docker stack services sre-app`
- `docker stack ps sre-app`
- frontend and backend services running in Swarm

## DigitalOcean Terraform Deployment

### Files

- `infra/terraform/main.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf`
- `infra/terraform/terraform.tfvars.example`

### Steps

1. Create a local ignored `infra/terraform/terraform.tfvars` from `infra/terraform/terraform.tfvars.example`.
2. Fill in your token and SSH key fingerprint.
3. Initialize Terraform:

```bash
cd infra/terraform
terraform init
```

4. Review the plan:

```bash
terraform plan
```

5. Apply the infrastructure:

```bash
terraform apply
```

6. Save the output public IP:

```bash
terraform output droplet_public_ip
```

### Droplet Setup

After Terraform creates the Droplet:

1. SSH into the server.
2. Install Docker Engine and Docker Compose plugin.
3. If you also want Docker Stack evidence, initialize Swarm:

```bash
docker swarm init
```
4. Clone the repository.
5. Run:

```bash
docker compose up -d --build
```

6. Confirm the frontend is reachable on `http://PUBLIC_IP`.
7. Access monitoring only through SSH tunneling:

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 root@PUBLIC_IP
```

8. Open locally in your browser:
   - `http://localhost:3000`
   - `http://localhost:9090`

If you deploy with Docker Stack on the Droplet instead of Docker Compose, use:

```bash
ssh -L 3001:127.0.0.1:3001 -L 9091:127.0.0.1:9091 root@PUBLIC_IP
```

## Screenshot Notes

Add screenshots to the final PDF for:
- Terraform `plan`
- Terraform `apply`
- Terraform public IP output
- Running application on the Droplet

See also: [docs/security-guidelines.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/security-guidelines.md)
