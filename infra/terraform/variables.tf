variable "do_token" {
  description = "DigitalOcean API token."
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name prefix used for Terraform resources."
  type        = string
  default     = "sre-app"
}

variable "region" {
  description = "DigitalOcean region slug."
  type        = string
  default     = "fra1"
}

variable "droplet_size" {
  description = "Droplet size slug."
  type        = string
  default     = "s-1vcpu-2gb"
}

variable "image" {
  description = "Droplet image slug."
  type        = string
  default     = "ubuntu-22-04-x64"
}

variable "ssh_key_fingerprint" {
  description = "Fingerprint of an SSH key already uploaded to DigitalOcean."
  type        = string
}
