import pytest
from external_resources_io.input import parse_model

from er_aws_vpc_endpoint_service.input import AppInterfaceInput


@pytest.fixture
def base_input() -> dict:
    return {
        "data": {
            "region": "us-east-1",
            "identifier": "myservice-vpce-service",
            "openshift_service_name": "myservice",
            "tags": {
                "managed_by_integration": "external_resources",
                "cluster": "appsret01ue1",
                "namespace": "myservice-stage",
                "environment": "production",
                "app": "myservice",
            },
        },
        "provision": {
            "provision_provider": "aws",
            "provisioner": "appsret01ue1",
            "provider": "vpc-endpoint-service",
            "identifier": "myservice-vpce-service",
            "target_cluster": "appsret01ue1",
            "target_namespace": "myservice-stage",
            "target_secret_name": "myservice-vpce-service",
            "module_provision_data": {
                "tf_state_bucket": "external-resources-terraform-state-dev",
                "tf_state_region": "us-east-1",
                "tf_state_dynamodb_table": "external-resources-terraform-lock",
                "tf_state_key": "aws/appsret01ue1/vpc-endpoint-service/myservice-vpce-service/terraform.tfstate",
            },
        },
    }


@pytest.fixture
def ai_input(base_input: dict) -> AppInterfaceInput:
    return parse_model(AppInterfaceInput, base_input)
