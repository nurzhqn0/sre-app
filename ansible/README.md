# Ansible VM Deployment

This directory targets a single-node VM. Keep real VM values in a local ignored inventory file.

- host: set in `ansible/inventory.local.ini`
- SSH user: set in `ansible/inventory.local.ini`
- deploy path: `/opt/sre-app`
- domain: set in `ansible/inventory.local.ini`
- Let's Encrypt email: set in `ansible/inventory.local.ini`

Create `ansible/inventory.local.ini` from this template:

```ini
[sre_demo]
sre-vm ansible_host=YOUR_VM_IP ansible_user=YOUR_SSH_USER ansible_python_interpreter=/usr/bin/python3

[sre_demo:vars]
deploy_path=/opt/sre-app
git_repo=https://github.com/nurzhqn0/sre-app.git
git_version=main
app_domain=YOUR_DOMAIN
acme_email=YOUR_EMAIL
```

`ansible/inventory.local.ini` is ignored by git so public IPs, private hostnames, users, domains, and email addresses are not committed.

Do not deploy with `ansible/inventory.ini`; it intentionally contains placeholders for syntax checks and examples only.

## Syntax Check

```bash
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/site.yml
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/k8s.yml
```

## Deploy Docker Compose

```bash
ansible-playbook -i ansible/inventory.local.ini ansible/site.yml
```

The Compose playbook installs Docker, checks out the repository to `/opt/sre-app`, writes `.env`, validates `docker-compose.yml`, and runs `docker compose up -d --build`.

## Deploy k3s

```bash
ansible-playbook -i ansible/inventory.local.ini ansible/k8s.yml
```

The k3s playbook installs Docker, k3s, and cert-manager if needed, checks out the repository, sets the ingress host and Let's Encrypt email, builds the app images on the VM, imports them into k3s containerd, applies `k8s/`, and prints pod/service/ingress status.

Override defaults with extra vars when needed:

```bash
ansible-playbook -i ansible/inventory.local.ini ansible/k8s.yml \
  -e app_domain=YOUR_DOMAIN \
  -e acme_email=YOUR_EMAIL \
  -e git_version=main
```
