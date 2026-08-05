locals {
  # The NLB is tagged by the OpenShift cloud controller with the service's namespace/name.
  # provision.target_namespace is the namespace of the ERv2 resource, which must match
  # the namespace of the OpenShift Service that created the NLB.
  nlb_service_tag = "${var.provision.target_namespace}/${var.openshift_service_name}"
  tags            = merge(var.tags, { Name = "vpces-${var.identifier}" })
}

data "aws_lb" "openshift" {
  tags = {
    "kubernetes.io/service-name" = local.nlb_service_tag
  }
}

resource "aws_vpc_endpoint_service" "this" {
  acceptance_required        = false
  network_load_balancer_arns = [data.aws_lb.openshift.arn]
  allowed_principals         = var.allowed_principal_arns
  supported_ip_address_types = ["ipv4"]
  private_dns_name           = var.private_dns_name
  tags                       = local.tags
}
