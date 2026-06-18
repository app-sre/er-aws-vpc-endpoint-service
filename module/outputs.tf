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

output "private_dns_verification_record_name" {
  description = "The DNS record name for domain ownership verification"
  value       = try(aws_vpc_endpoint_service.this.private_dns_name_configuration[0].name, null)
}

output "private_dns_verification_record_type" {
  description = "The DNS record type for domain ownership verification"
  value       = try(aws_vpc_endpoint_service.this.private_dns_name_configuration[0].type, null)
}

output "private_dns_verification_record_value" {
  description = "The DNS record value for domain ownership verification"
  value       = try(aws_vpc_endpoint_service.this.private_dns_name_configuration[0].value, null)
}

output "private_dns_verification_state" {
  description = "The verification state of the private DNS name (pendingVerification, verified, failed)"
  value       = try(aws_vpc_endpoint_service.this.private_dns_name_configuration[0].state, null)
}
