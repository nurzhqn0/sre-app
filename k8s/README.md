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
