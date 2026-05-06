# SRE App: Containerized Microservices, Terraform, and Incident Response

This project implements a microservices-based e-commerce style platform for an SRE assignment. It combines FastAPI services, a React frontend served by Nginx, PostgreSQL, Docker Compose for local orchestration, Docker Stack for Swarm deployment, Prometheus, Grafana, Terraform for DigitalOcean, and a structured incident response simulation.

## Architecture

![alt text](/docs/image.png)

## Services

- `frontend`: React user interface served through Nginx on port `80`
- `auth-service`: registration and login
- `user-service`: user profile and user list
- `product-service`: product catalog
- `order-service`: order creation and listing
- `chat-service`: WebSocket chat and message history
- `postgres`: shared relational database
- `prometheus`: metrics scraping on local port `9090`
- `grafana`: dashboards on local port `3000`
- `cadvisor`: container CPU, memory, and restart signal metrics for Prometheus

## Quick Start

1. Create a local `.env` from `.env.example` if you want to override defaults or set non-demo secrets.
2. Start the full platform:

```bash
docker compose up -d --build
```

Pre-deployment validation for the Assignment 6 automation workflow:

```bash
python3 scripts/validate_compose_config.py -f docker-compose.yml
```

3. Open the application:
   - Frontend: [http://localhost](http://localhost)
   - Grafana: [http://localhost:3000](http://localhost:3000)
   - Prometheus: [http://localhost:9090](http://localhost:9090)

Monitoring note:
- Grafana and Prometheus are bound to `127.0.0.1`
- they are reachable only on the local machine unless you forward them over SSH

4. Stop the stack:

```bash
docker compose down
```

## Docker Stack Deployment

The repository also supports full Docker Swarm deployment through [docker-stack.yml](/Users/myrzanizimbetov/Desktop/sre-app/docker-stack.yml). The stack deploys:

- `frontend`
- `auth-service`
- `user-service`
- `product-service`
- `order-service`
- `chat-service`
- `postgres`
- `prometheus`
- `grafana`

1. Initialize Swarm on the target host if it is not already enabled:

```bash
docker swarm init
```

2. Build the application images locally for the Swarm node:

```bash
./scripts/build-stack-images.sh
```

3. Deploy the stack:

```bash
docker stack deploy -c docker-stack.yml sre-app
```

Default Swarm published ports are set to avoid common local conflicts:

- frontend: `8080`
- Grafana: `3001`
- Prometheus: `9091`

When the stack is deployed on a remote server, keep monitoring private:
- expose the frontend publicly as needed
- keep Grafana and Prometheus behind the Terraform firewall
- access monitoring only through an SSH tunnel to `127.0.0.1:3001` and `127.0.0.1:9091`

If you still need different ports, override them during deployment:

```bash
STACK_HTTP_PORT=8081 STACK_GRAFANA_PORT=3002 STACK_PROMETHEUS_PORT=9092 docker stack deploy -c docker-stack.yml sre-app
```

4. Inspect services:

```bash
docker stack services sre-app
docker stack ps sre-app
```

5. If the stack is running on a remote host, create an SSH tunnel for monitoring:

```bash
ssh -L 3001:127.0.0.1:3001 -L 9091:127.0.0.1:9091 root@YOUR_PUBLIC_IP
```

Then open locally:
- `http://localhost:3001`
- `http://localhost:9091`

6. Remove the stack when finished:

```bash
docker stack rm sre-app
```

## Terraform Infrastructure

Terraform configuration is included in [infra/terraform](/Users/myrzanizimbetov/Desktop/sre-app/infra/terraform) and provisions the infrastructure required by the assignment on DigitalOcean.

Version targets used in this repo:
- Terraform CLI `1.14.x`
- DigitalOcean Terraform provider `2.69.x`
- Grafana image `13.0.1`
- Prometheus image `3.11.2`

Included files:
- `main.tf`
- `variables.tf`
- `outputs.tf`
- `terraform.tfvars.example`

Provisioned resources:
- one `digitalocean_droplet`
- one `digitalocean_firewall`

Opened ports:
- `22` for SSH
- `80` for the frontend

Monitoring access policy:
- Grafana and Prometheus are intended to be accessed only through an SSH tunnel
- the Terraform firewall does not expose monitoring ports publicly
- Docker Compose binds monitoring ports to `127.0.0.1` on the host

Basic workflow:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
terraform output droplet_public_ip
```

Before running Terraform:
1. Create a local ignored `infra/terraform/terraform.tfvars` from `infra/terraform/terraform.tfvars.example`.
2. Add your DigitalOcean API token.
3. Set the uploaded SSH key fingerprint.
4. Review the selected region, Droplet size, and image values.

After Terraform creates the Droplet:
1. SSH into the new server.
2. Install Docker Engine and Docker Compose.
3. Clone this repository.
4. Run `docker compose up -d --build`.
5. Verify public access on port `80`.
6. Use SSH tunneling for monitoring access:

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 root@YOUR_PUBLIC_IP
```

7. Open locally in your browser:
   - `http://localhost:3000`
   - `http://localhost:9090`

## Default Demo Flow

1. Register a new user in the frontend.
2. Browse products loaded from `product-service`.
3. Create an order from the Orders view.
4. Open the Chat view in two browser windows and exchange WebSocket messages.
5. Open the Status view to confirm health and observability coverage.

## Incident Simulation

Break the `order-service` database configuration with the incident override:

```bash
docker compose -f docker-compose.yml -f docker-compose.incident.yml up -d order-service
```

Restore healthy configuration:

```bash
docker compose up -d order-service
```

Detailed response steps are documented in [docs/incident-report.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/incident-report.md) and [docs/postmortem.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/postmortem.md).

For Swarm-based incident simulation, deploy the override with:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.incident.yml sre-app
```

## Documentation

- Setup and deployment: [docs/deployment-guide.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/deployment-guide.md)
- Security guidance: [docs/security-guidelines.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/security-guidelines.md)
- Assignment 6 automation and capacity planning: [docs/assignment-6-automation-capacity.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/assignment-6-automation-capacity.md)
- Terraform explanation: [docs/assignment-5-terraform.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/assignment-5-terraform.md)
- Incident response report: [docs/incident-report.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/incident-report.md)
- Postmortem: [docs/postmortem.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/postmortem.md)
- Submission checklist: [docs/final-submission-checklist.md](/Users/myrzanizimbetov/Desktop/sre-app/docs/final-submission-checklist.md)
