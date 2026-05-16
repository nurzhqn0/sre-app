# SRE Microservices Project

End-term SRE project with six FastAPI microservices, React/Nginx frontend, PostgreSQL, Docker Compose, Docker Swarm, Kubernetes, Terraform, Ansible, Prometheus, Grafana, incident simulation, and capacity planning.

GitHub: <https://github.com/nurzhqn0/sre-app.git>

## Services

| Service | Purpose | Port |
| --- | --- | --- |
| `frontend` | React UI served by Nginx | `80` |
| `auth-service` | Register/login, JWT auth | `8001` |
| `user-service` | User profile | `8002` |
| `product-service` | Product catalog | `8003` |
| `order-service` | Order creation/listing | `8004` |
| `chat-service` | WebSocket chat | `8005` |
| `payment-service` | Simulated payment authorization | `8006` |
| `postgres` | Main database | `5432` |
| `prometheus` | Metrics and alerts | `9090` Compose, `9091` Swarm |
| `grafana` | Dashboards | `3000` Compose, `3001` Swarm |

## Quick Validation

```bash
python3 scripts/validate_compose_config.py -f docker-compose.yml
cd frontend && npm run build && cd ..
docker compose config --quiet
```

Optional checks:

```bash
ruby -e 'require "yaml"; Dir["k8s/**/*.yaml"].each { |f| YAML.load_stream(File.read(f)) }; puts "k8s yaml ok"'
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/site.yml
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/k8s.yml
```

## Run With Docker Compose

Start:

```bash
docker compose up -d --build
```

Open:

- Frontend: <http://localhost>
- Grafana: <http://localhost:3000>
- Prometheus: <http://localhost:9090>

Stop:

```bash
docker compose down
```

## Demo Flow

1. Register or log in.
2. Open Products and confirm catalog data.
3. Open Orders and create an order.
4. Open Payments and authorize payment for the order.
5. Open Chat and send a message.
6. Open Status and confirm all services are healthy.

## Incident Simulation

Break `order-service` database config:

```bash
docker compose -f docker-compose.yml -f docker-compose.incident.yml up -d order-service
```

Expected result:

- order workflow fails
- `order-service` health becomes unhealthy
- Prometheus/Grafana show degradation

Recover:

```bash
docker compose up -d order-service
```

Useful checks:

```bash
docker compose logs order-service
curl -s 'http://localhost:9090/api/v1/query?query=service_health_status{service="order-service"}'
```

## Docker Swarm

Start Swarm:

```bash
docker swarm init
```

Build local stack images:

```bash
./scripts/build-stack-images.sh
```

Deploy:

```bash
docker stack deploy -c docker-stack.yml sre-app
```

Check:

```bash
docker stack services sre-app
docker stack ps sre-app
```

Capacity/scaling variant:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.capacity.yml sre-app
```

Incident variant:

```bash
docker stack deploy -c docker-stack.yml -c docker-stack.incident.yml sre-app
```

Stop:

```bash
docker stack rm sre-app
```

## Kubernetes

If `kubectl` says `localhost:8080 refused`, no cluster/context is running.

Check:

```bash
kubectl config get-contexts
kubectl config current-context
```

### Option A: Minikube

Start Docker Desktop first:

```bash
open -a Docker
docker ps
```

Start Minikube:

```bash
minikube start --driver=docker
kubectl config use-context minikube
kubectl get nodes
```

Build images inside Minikube:

```bash
eval $(minikube docker-env)
./scripts/build-stack-images.sh
```

Deploy:

```bash
kubectl apply -f k8s/
kubectl -n sre-app get pods,svc
```

Open:

```bash
kubectl -n sre-app port-forward svc/frontend 8080:80
```

Frontend: <http://localhost:8080>

Monitoring:

```bash
kubectl -n sre-app port-forward svc/prometheus 9090:9090
kubectl -n sre-app port-forward svc/grafana 3000:3000
```

Stop app:

```bash
kubectl delete -f k8s/
```

Stop Minikube:

```bash
minikube stop
```

Delete Minikube cluster:

```bash
minikube delete
```

Return shell to normal Docker:

```bash
eval $(minikube docker-env -u)
```

### Option B: Docker Desktop Kubernetes

Enable Kubernetes:

```text
Docker Desktop -> Settings -> Kubernetes -> Enable Kubernetes -> Apply & Restart
```

Use context:

```bash
kubectl config use-context docker-desktop
kubectl get nodes
```

Build and deploy:

```bash
./scripts/build-stack-images.sh
kubectl apply -f k8s/
kubectl -n sre-app get pods,svc
```

Open:

```bash
kubectl -n sre-app port-forward svc/frontend 8080:80
```

### Optional Kubernetes cAdvisor

cAdvisor is optional in Kubernetes. It can fail on Docker Desktop/Minikube because host runtime paths may not exist.

Apply only if needed:

```bash
kubectl apply -f k8s/optional/cadvisor.yaml
kubectl -n sre-app get pods -l app=cadvisor
```

The optional manifest disables service-account token mounting because cAdvisor mounts host `/var/run`; on Docker Desktop this avoids a common read-only filesystem conflict at `/var/run/secrets/kubernetes.io/serviceaccount`.

Remove if failing:

```bash
kubectl delete -f k8s/optional/cadvisor.yaml
```

The core Kubernetes demo does not require cAdvisor.

## Ansible

Install:

```bash
brew install ansible
```

Syntax check:

```bash
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/site.yml
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/k8s.yml
```

Deploy Docker Compose stack:

```bash
ansible-playbook -i ansible/inventory.ini ansible/site.yml
```

Deploy Kubernetes manifests:

```bash
ansible-playbook -i ansible/inventory.ini ansible/k8s.yml
```

Stop Ansible Compose deployment:

```bash
docker compose down
```

### Ansible on Linux VPS with k3s

If Kubernetes pods show `ImagePullBackOff` or `ErrImagePull` for images like `sre-app/auth-service:latest`, k3s cannot see the local Docker images.

On the VPS:

```bash
apt update
apt install -y git docker.io
systemctl enable --now docker
curl -sfL https://get.k3s.io | sh -
```

Clone and enter the repo:

```bash
git clone https://github.com/nurzhqn0/sre-app.git
cd sre-app
```

Build app images on the VPS:

```bash
./scripts/build-stack-images.sh
```

Import images into k3s containerd:

```bash
chmod +x scripts/import-k3s-images.sh
./scripts/import-k3s-images.sh
```

Apply manifests:

```bash
ansible-playbook -i ansible/inventory.ini ansible/k8s.yml
```

Restart deployments after importing images:

```bash
kubectl -n sre-app rollout restart deployment
kubectl -n sre-app get pods
```

Expose frontend on a VPS:

```bash
kubectl -n sre-app patch svc frontend -p '{"spec":{"type":"NodePort","ports":[{"port":80,"targetPort":80,"nodePort":30080}]}}'
```

Open:

```text
http://YOUR_SERVER_IP:30080
```

## Terraform

Terraform provisions a DigitalOcean droplet and firewall.

Files:

- `infra/terraform/main.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf`
- `infra/terraform/terraform.tfvars.example`

Run:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
terraform output droplet_public_ip
```

Do not commit real `terraform.tfvars` or secrets.

## Monitoring

Prometheus:

- `monitoring/prometheus/prometheus.yml`
- `monitoring/prometheus/prometheus-stack.yml`
- `monitoring/prometheus/alerts.yml`

Grafana:

- `monitoring/grafana/provisioning/datasources/datasource.yml`
- `monitoring/grafana/provisioning/dashboards/dashboard.yml`
- `monitoring/grafana/dashboards/platform-overview.json`

Backend endpoints:

```text
/health
/metrics
```

Main SLOs:

| SLI | SLO |
| --- | --- |
| Availability | `>= 99%` |
| p95 latency | `<= 200 ms` |
| Error rate | `<= 1%` |
| Success rate | `>= 99%` |

## Important Files

| Path | Purpose |
| --- | --- |
| `docs/end-term-project.md` | Final project report |
| `docs/defence-guide.md` | Defence preparation |
| `docs/incident-report.md` | Incident report |
| `docs/postmortem.md` | Postmortem |
| `docker-compose.yml` | Local deployment |
| `docker-stack.yml` | Swarm deployment |
| `k8s/` | Kubernetes manifests |
| `ansible/` | Ansible automation |
| `infra/terraform/` | Terraform infrastructure |
| `scripts/validate_compose_config.py` | Pre-deployment validation |
| `scripts/load_test.py` | Load test helper |

## Stop and Delete Everything

Stop a running port-forward:

```bash
Ctrl + C
```

Stop Docker Compose:

```bash
docker compose down
```

Stop Docker Compose and delete volumes:

```bash
docker compose down -v
```

Remove Docker Swarm stack:

```bash
docker stack rm sre-app
```

Leave Docker Swarm mode after stack removal:

```bash
docker swarm leave --force
```

Delete Kubernetes app resources:

```bash
kubectl delete -f k8s/
```

Stop Kubernetes workloads without deleting resources:

```bash
kubectl scale deploy --all --replicas=0 -n sre-app
kubectl scale statefulset --all --replicas=0 -n sre-app
```

Start Kubernetes workloads again:

```bash
kubectl scale deploy --all --replicas=1 -n sre-app
kubectl scale statefulset --all --replicas=1 -n sre-app
```

Delete optional Kubernetes cAdvisor:

```bash
kubectl delete -f k8s/optional/cadvisor.yaml
```

Stop Minikube but keep the cluster:

```bash
minikube stop
```

Delete Minikube completely:

```bash
minikube delete
```

Return shell from Minikube Docker environment to normal Docker:

```bash
eval $(minikube docker-env -u)
```

Delete Kubernetes namespace directly if manifest deletion is stuck:

```bash
kubectl delete namespace sre-app
```

Remove locally built project images:

```bash
docker rmi \
  sre-app/auth-service:latest \
  sre-app/user-service:latest \
  sre-app/product-service:latest \
  sre-app/order-service:latest \
  sre-app/chat-service:latest \
  sre-app/payment-service:latest \
  sre-app/frontend:latest
```

## Defence Evidence Checklist

Capture screenshots or terminal output for:

- frontend running
- products, orders, payments, chat
- service health view
- Prometheus targets
- Grafana dashboard
- incident failure state
- recovery state
- Docker Swarm services
- Kubernetes pods/services
- Ansible syntax check or run output
- Terraform plan/apply output if cloud demo is used
