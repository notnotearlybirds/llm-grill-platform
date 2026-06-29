locals {
  name = "llmgrill-${var.run_id}"
}

resource "scaleway_iam_ssh_key" "keys" {
  count      = length(var.ssh_public_keys)
  name       = "${local.name}-key-${count.index}"
  public_key = var.ssh_public_keys[count.index]
}

resource "scaleway_instance_ip" "gpu" {}

# All GPU VM traffic is outbound (HF download, S3 upload, orchestrator callbacks).
# Inbound is dropped entirely except SSH from admin_cidrs (debug access).
resource "scaleway_instance_security_group" "gpu" {
  name                    = local.name
  zone                    = var.gpu_zone
  inbound_default_policy  = "drop"
  outbound_default_policy = "accept"

  dynamic "inbound_rule" {
    for_each = var.admin_cidrs
    content {
      action   = "accept"
      port     = 22
      protocol = "TCP"
      ip_range = inbound_rule.value
    }
  }
}

resource "scaleway_instance_server" "gpu" {
  name  = local.name
  type  = var.instance_type
  image = "ubuntu_noble_gpu_os_13_nvidia"
  zone  = var.gpu_zone

  ip_id             = scaleway_instance_ip.gpu.id
  security_group_id = scaleway_instance_security_group.gpu.id

  root_volume {
    size_in_gb            = 250
    delete_on_termination = true
  }

  user_data = {
    "cloud-init" = templatefile("${path.module}/cloud-init.tpl.yaml", {
      run_id                        = var.run_id
      orchestrator_url              = var.orchestrator_url
      hf_token                      = var.hf_token
      orchestrator_api_key          = var.orchestrator_api_key
      model                         = var.model
      engine                        = var.engine
      scenario_path                 = var.scenario_path
      gguf_file                     = var.gguf_file
      scenario_content              = var.scenario_content
      docker_image                  = var.docker_image
      download_timeout_seconds      = var.download_timeout_seconds
      engine_health_timeout_seconds = var.engine_health_timeout_seconds
    })
  }
}
