output "endpoint_service_name" {
  description = "The AWS service name for the VPC Endpoint Service (e.g., com.amazonaws.vpce.us-east-1.vpce-svc-xxx)"
  value       = aws_vpc_endpoint_service.this.service_name
}

output "endpoint_service_id" {
  description = "The ID of the VPC Endpoint Service"
  value       = aws_vpc_endpoint_service.this.id
}

output "nlb_arn" {
  description = "The ARN of the Network Load Balancer attached to the endpoint service"
  value       = data.aws_lb.openshift.arn
}

output "nlb_dns_name" {
  description = "The DNS name of the Network Load Balancer"
  value       = data.aws_lb.openshift.dns_name
}
