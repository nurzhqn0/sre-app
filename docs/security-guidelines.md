# Security Guidelines

## Never Commit To GitHub

- real DigitalOcean API tokens
- `.env`
- real `terraform.tfvars`
- private SSH keys or `.pem` files
- Terraform state files: `terraform.tfstate`, `terraform.tfstate.backup`, `.terraform/`
- real database passwords
- real JWT signing secrets
- real Grafana admin passwords

## Use Example Files In The Repository

- keep placeholders in `.env.example`
- keep placeholders in `infra/terraform/terraform.tfvars.example`
- keep live values only in local ignored files:
  - `.env`
  - `infra/terraform/terraform.tfvars`

## Safer Terraform Usage

Preferred local options:

1. Create a local ignored `infra/terraform/terraform.tfvars` based on the example file.
2. Or export sensitive Terraform variables through the shell:

```bash
export TF_VAR_do_token="your_digitalocean_token"
export TF_VAR_ssh_key_fingerprint="your_ssh_key_fingerprint"
```

## Screenshot Hygiene

Before submitting PDFs or pushing screenshots:

- blur tokens and passwords
- blur terminal history that shows secrets
- blur real public IPs if you do not want them exposed
- avoid capturing browser pages that reveal admin credentials

## Submission Rule

The GitHub version of the project should contain only code, configuration templates, and sanitized documentation.
