output "droplet_public_ip" {
  description = "Public IPv4 address of the SRE application Droplet."
  value       = digitalocean_droplet.sre_app.ipv4_address
}

output "droplet_name" {
  description = "Created Droplet name."
  value       = digitalocean_droplet.sre_app.name
}
