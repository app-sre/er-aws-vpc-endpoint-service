variable "allowed_principal_arns" {
  type = list(string)
}

variable "identifier" {
  type = string
}

variable "openshift_service_name" {
  type = string
}

variable "output_resource_name" {
  type    = string
  default = null
}

variable "region" {
  type = string
}

variable "tags" {
  type = map(any)
}
