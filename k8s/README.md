# Local Kubernetes Demo

These manifests deploy the SRE demo stack to a local Kubernetes cluster such as Docker Desktop, kind, or minikube.

Build the images locally before applying the manifests:

```bash
./scripts/build-stack-images.sh
```

Apply everything:

```bash
kubectl apply -f k8s/
```

For HTTPS, install cert-manager before applying the manifests because `k8s/60-cert-manager-issuer.yaml` uses the `ClusterIssuer` CRD:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.20.2/cert-manager.yaml
kubectl -n cert-manager rollout status deployment/cert-manager
kubectl -n cert-manager rollout status deployment/cert-manager-cainjector
kubectl -n cert-manager rollout status deployment/cert-manager-webhook
kubectl apply -f k8s/
```

After deployment, check the Let's Encrypt certificate:

```bash
kubectl -n sre-app get certificate
kubectl -n sre-app describe certificate frontend-tls
kubectl -n sre-app get secret frontend-tls
```

Check status:

```bash
kubectl -n sre-app get pods,svc
```

Local access options:

```bash
kubectl -n sre-app port-forward svc/frontend 8080:80
kubectl -n sre-app port-forward svc/grafana 3000:3000
kubectl -n sre-app port-forward svc/prometheus 9090:9090
```

Then open:

- frontend: `http://localhost:8080`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

The secrets in these manifests are demo values for local grading only.

## Optional cAdvisor

cAdvisor is optional for Kubernetes in this project. Docker Compose still includes cAdvisor by default, but local Kubernetes clusters often use different container runtimes or hide host paths such as `/var/lib/docker`, which can make the cAdvisor DaemonSet fail on Docker Desktop or Minikube.

The default Kubernetes deployment therefore starts the app, Prometheus, and Grafana without cAdvisor.

If your local cluster supports cAdvisor host mounts, apply it separately:

```bash
kubectl apply -f k8s/optional/cadvisor.yaml
kubectl -n sre-app get pods -l app=cadvisor
```

If cAdvisor fails, remove it without affecting the application:

```bash
kubectl delete -f k8s/optional/cadvisor.yaml
```

## Incident Simulation

Break `order-service` database connectivity by applying an incident patch with an invalid PostgreSQL hostname:

```bash
kubectl apply -f k8s/incident/order-service-broken-db.yaml
kubectl -n sre-app rollout status deployment/order-service --timeout=90s
```

Expected result:

- order creation and order listing fail
- `order-service` readiness fails
- rollout status times out or reports progress deadline exceeded
- Prometheus target and health metrics show degradation
- Grafana shows order-service impact

Useful checks:

```bash
kubectl -n sre-app get pods -l app=order-service
kubectl -n sre-app logs deployment/order-service --tail=100
kubectl -n sre-app port-forward svc/prometheus 9090:9090
curl -s 'http://localhost:9090/api/v1/query?query=service_health_status{service="order-service"}'
```

Recover by reapplying the normal service manifest and waiting for rollout:

```bash
kubectl apply -f k8s/20-services.yaml
kubectl -n sre-app rollout status deployment/order-service --timeout=120s
```
