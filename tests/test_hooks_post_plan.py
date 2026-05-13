from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from external_resources_io.terraform import (
    Action,
    ResourceChange,
    TerraformJsonPlanParser,
)

from er_aws_vpc_endpoint_service.input import AppInterfaceInput
from hooks.post_plan import VpcEndpointServicePlanValidator


@pytest.fixture
def mock_plan() -> MagicMock:
    mock_inner = MagicMock()
    mock_inner.resource_changes = []
    parser = MagicMock(spec=TerraformJsonPlanParser)
    parser.plan = mock_inner
    return parser


@pytest.fixture
def mock_aws_api() -> Iterator[MagicMock]:
    with patch("hooks.post_plan.AWSApi") as mock:
        yield mock


def _make_delete_change(
    service_id: str, address: str = "aws_vpc_endpoint_service.this"
) -> MagicMock:
    return MagicMock(
        spec=ResourceChange,
        type="aws_vpc_endpoint_service",
        address=address,
        change=MagicMock(
            actions=[Action.ActionDelete],
            before={"id": service_id},
        ),
    )


def test_validate_no_changes(
    ai_input: AppInterfaceInput,
    mock_plan: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    validator = VpcEndpointServicePlanValidator(mock_plan, ai_input)
    assert validator.validate()
    assert not validator.errors
    mock_aws_api.return_value.get_active_endpoint_connections.assert_not_called()


def test_validate_delete_no_active_connections(
    ai_input: AppInterfaceInput,
    mock_plan: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    mock_aws_api.return_value.get_active_endpoint_connections.return_value = []
    mock_plan.plan.resource_changes = [_make_delete_change("vpce-svc-0123")]
    validator = VpcEndpointServicePlanValidator(mock_plan, ai_input)
    assert validator.validate()
    assert not validator.errors


def test_validate_delete_with_active_connections(
    ai_input: AppInterfaceInput,
    mock_plan: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    mock_aws_api.return_value.get_active_endpoint_connections.return_value = [
        "vpce-0aaa",
        "vpce-0bbb",
    ]
    mock_plan.plan.resource_changes = [_make_delete_change("vpce-svc-0123")]
    validator = VpcEndpointServicePlanValidator(mock_plan, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "vpce-0aaa" in validator.errors[0]
    assert "vpce-0bbb" in validator.errors[0]


def test_validate_delete_missing_service_id(
    ai_input: AppInterfaceInput,
    mock_plan: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    change = MagicMock(
        spec=ResourceChange,
        type="aws_vpc_endpoint_service",
        address="aws_vpc_endpoint_service.this",
        change=MagicMock(actions=[Action.ActionDelete], before={}),
    )
    mock_plan.plan.resource_changes = [change]
    validator = VpcEndpointServicePlanValidator(mock_plan, ai_input)
    assert not validator.validate()
    assert "Cannot determine service ID" in validator.errors[0]
    mock_aws_api.return_value.get_active_endpoint_connections.assert_not_called()


def test_validate_update_not_blocked(
    ai_input: AppInterfaceInput,
    mock_plan: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    mock_plan.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_vpc_endpoint_service",
            address="aws_vpc_endpoint_service.this",
            change=MagicMock(actions=[Action.ActionUpdate]),
        )
    ]
    validator = VpcEndpointServicePlanValidator(mock_plan, ai_input)
    assert validator.validate()
    assert not validator.errors
    mock_aws_api.return_value.get_active_endpoint_connections.assert_not_called()


def test_validate_non_endpoint_service_change_ignored(
    ai_input: AppInterfaceInput,
    mock_plan: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    other = MagicMock(spec=ResourceChange, type="aws_lb")
    mock_plan.plan.resource_changes = [other]
    validator = VpcEndpointServicePlanValidator(mock_plan, ai_input)
    assert validator.validate()
    assert not validator.errors
    mock_aws_api.return_value.get_active_endpoint_connections.assert_not_called()
