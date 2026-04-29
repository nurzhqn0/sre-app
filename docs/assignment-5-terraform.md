# Assignment 5: Terraform Implementation

## Objective

Provision the deployment host using Terraform in a reproducible way on DigitalOcean.

## Resources Created

- one `digitalocean_droplet`
- one `digitalocean_firewall`

## Version Targets

- Terraform CLI `1.14.x`
- DigitalOcean provider `2.69.x`
- These constraints are declared in `infra/terraform/main.tf`

## Ports Opened

- `22` for SSH
- `80` for the frontend

## Monitoring Access Model

- Grafana and Prometheus are not intended to be publicly exposed
- monitoring access is performed through SSH port forwarding
- the Terraform firewall only exposes SSH and HTTP publicly

## Commands

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## Output

The Terraform configuration exports:
- `droplet_public_ip`
- `droplet_name`

## Explanation

- `main.tf` defines the provider, Droplet, and firewall rules.
- `variables.tf` centralizes token, region, size, image, and SSH key values.
- `outputs.tf` exposes the public IP required for deployment and evidence.
- `terraform.tfvars.example` provides a safe template, while the real `terraform.tfvars` should remain local and ignored.

## Evidence To Capture

Add screenshots of:
- `terraform init`
- `terraform plan`
- `terraform apply`
- `terraform output droplet_public_ip`
- application reachable via the provisioned IP
