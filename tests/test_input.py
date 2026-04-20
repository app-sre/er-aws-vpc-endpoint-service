import pytest
from pydantic import ValidationError

from er_aws_vpc_endpoint_service.input import AppInterfaceInput


def test_basic_input(base_input: dict) -> None:
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.identifier == "myservice-vpce-service"
    assert ai_input.data.openshift_service_name == "myservice"
    assert ai_input.data.allowed_principal_arns == []


def test_allowed_principal_arns(base_input: dict) -> None:
    base_input["data"]["allowed_principal_arns"] = [
        "arn:aws:iam::123456789012:user/appsret02ue1-terraform"
    ]
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.allowed_principal_arns == [
        "arn:aws:iam::123456789012:user/appsret02ue1-terraform"
    ]


def test_allowed_principal_arns_multiple(base_input: dict) -> None:
    base_input["data"]["allowed_principal_arns"] = [
        "arn:aws:iam::111111111111:user/cluster-a-terraform",
        "arn:aws:iam::222222222222:user/cluster-b-terraform",
    ]
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.allowed_principal_arns == [
        "arn:aws:iam::111111111111:user/cluster-a-terraform",
        "arn:aws:iam::222222222222:user/cluster-b-terraform",
    ]


def test_data_fields(base_input: dict) -> None:
    ai_input = AppInterfaceInput.model_validate(base_input)
    assert ai_input.data.region == "us-east-1"
    assert ai_input.data.identifier == "myservice-vpce-service"
    assert ai_input.data.openshift_service_name == "myservice"
    assert ai_input.data.tags == base_input["data"]["tags"]


def test_missing_required_field(base_input: dict) -> None:
    del base_input["data"]["openshift_service_name"]
    with pytest.raises(ValidationError):
        AppInterfaceInput.model_validate(base_input)
