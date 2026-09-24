import json
from pathlib import Path
from unittest.mock import patch

import pytest
from external_resources_io.config import Action, Config

from er_aws_vpc_endpoint_service.input import AppInterfaceInput
from hooks.post_apply import VpcEndpointServicePostApply, main


@pytest.fixture
def post_apply(
    ai_input: AppInterfaceInput, tmp_path: Path
) -> VpcEndpointServicePostApply:
    output_file = tmp_path / "output.json"
    output_file.write_text(
        json.dumps({"endpoint_service_id": {"value": "vpce-svc-123"}}),
        encoding="utf-8",
    )
    return VpcEndpointServicePostApply(
        Config(DRY_RUN=False, OUTPUTS_FILE=str(output_file)), ai_input
    )


@pytest.mark.parametrize(
    ("dry_run", "action"),
    [(True, Action.DESTROY), (False, Action.DESTROY)],
)
def test_main_skips_non_apply(*, dry_run: bool, action: Action) -> None:
    with (
        patch(
            "hooks.post_apply.Config",
            return_value=Config(DRY_RUN=dry_run, ACTION=action),
        ),
        patch("hooks.post_apply.read_input_from_file") as read_input,
    ):
        main()
    read_input.assert_not_called()


def test_main_calls_removal(base_input: dict) -> None:
    with (
        patch("hooks.post_apply.Config", return_value=Config(DRY_RUN=True)),
        patch("hooks.post_apply.read_input_from_file", return_value=base_input),
        patch("hooks.post_apply.VpcEndpointServicePostApply") as handler,
    ):
        main()
    handler.return_value.remove_private_dns_name.assert_called_once_with()


def test_configured_name_is_unchanged(post_apply: VpcEndpointServicePostApply) -> None:
    post_apply.input.data.private_dns_name = "test.devshift.net"
    with patch("hooks.post_apply.AWSApi") as aws_api:
        post_apply.remove_private_dns_name()
    aws_api.assert_not_called()


def test_missing_service_id_is_ignored(post_apply: VpcEndpointServicePostApply) -> None:
    Path(post_apply.config.outputs_file).write_text("{}", encoding="utf-8")
    with patch("hooks.post_apply.AWSApi") as aws_api:
        post_apply.remove_private_dns_name()
    aws_api.assert_not_called()


def test_no_private_dns_is_unchanged(post_apply: VpcEndpointServicePostApply) -> None:
    with patch("hooks.post_apply.AWSApi") as aws_api:
        ec2 = aws_api.return_value.ec2_client
        ec2.describe_vpc_endpoint_service_configurations.return_value = {
            "ServiceConfigurations": [{}]
        }
        post_apply.remove_private_dns_name()
    ec2.describe_vpc_endpoint_service_configurations.assert_called_once_with(
        ServiceIds=["vpce-svc-123"]
    )
    ec2.modify_vpc_endpoint_service_configuration.assert_not_called()


def test_missing_service_configuration_fails(
    post_apply: VpcEndpointServicePostApply,
) -> None:
    with patch("hooks.post_apply.AWSApi") as aws_api:
        aws_api.return_value.ec2_client.describe_vpc_endpoint_service_configurations.return_value = {
            "ServiceConfigurations": []
        }
        with pytest.raises(RuntimeError, match="vpce-svc-123 was not found"):
            post_apply.remove_private_dns_name()


def test_private_dns_is_removed(post_apply: VpcEndpointServicePostApply) -> None:
    with patch("hooks.post_apply.AWSApi") as aws_api:
        ec2 = aws_api.return_value.ec2_client
        ec2.describe_vpc_endpoint_service_configurations.return_value = {
            "ServiceConfigurations": [{"PrivateDnsName": "test.devshift.net"}]
        }
        with pytest.raises(SystemExit) as exc:
            post_apply.remove_private_dns_name()
    assert exc.value.code == 1
    ec2.modify_vpc_endpoint_service_configuration.assert_called_once_with(
        ServiceId="vpce-svc-123", RemovePrivateDnsName=True
    )
