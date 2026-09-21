import json
import subprocess  # ruff: ignore[suspicious-subprocess-import] - Terraform is invoked without a shell
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from external_resources_io.config import Config

from er_aws_vpc_endpoint_service.input import AppInterfaceInput
from hooks.post_output import VERIFICATION_OUTPUTS, sync_private_dns_outputs


@pytest.fixture
def config(tmp_path: Path) -> Config:
    output_path = tmp_path / "output.json"
    output_path.write_text(
        json.dumps({"endpoint_service_id": {"value": "vpce-svc-123"}})
    )
    return Config(
        DRY_RUN=False,
        ACTION="Apply",
        OUTPUTS_FILE=str(output_path),
        TERRAFORM_CMD="terraform -chdir=/work/module",
        TF_VARS_FILE="/work/module/terraform.tfvars.json",
    )


@pytest.fixture
def dns_input(ai_input: AppInterfaceInput) -> AppInterfaceInput:
    ai_input.data.private_dns_name = "test.devshift.net"
    return ai_input


@pytest.fixture
def outputs() -> dict:
    return {
        "endpoint_service_id": {"value": "vpce-svc-123"},
        "private_dns_verification_record_name": {"value": "_verification"},
        "private_dns_verification_record_type": {"value": "TXT"},
        "private_dns_verification_record_value": {"value": "vpce:verification"},
        "private_dns_verification_state": {"value": "pendingVerification"},
    }


@pytest.mark.parametrize("skip", ["dry_run", "destroy", "no_dns", "complete"])
def test_skip_refresh(
    config: Config, dns_input: AppInterfaceInput, outputs: dict, skip: str
) -> None:
    if skip == "dry_run":
        config.dry_run = True
    elif skip == "destroy":
        config = Config(**{**config.model_dump(by_alias=True), "ACTION": "Destroy"})
    elif skip == "no_dns":
        dns_input.data.private_dns_name = None
    else:
        Path(config.outputs_file).write_text(json.dumps(outputs), encoding="utf-8")
    with patch("hooks.post_output.subprocess.run") as run:
        sync_private_dns_outputs(config, dns_input)
    run.assert_not_called()


@pytest.mark.parametrize("missing", [None, *VERIFICATION_OUTPUTS])
def test_refresh_recovers_missing_output(
    config: Config, dns_input: AppInterfaceInput, outputs: dict, missing: str | None
) -> None:
    Path(config.outputs_file).write_text(
        json.dumps({
            k: v
            for k, v in outputs.items()
            if k != missing and (missing is not None or k not in VERIFICATION_OUTPUTS)
        }),
        encoding="utf-8",
    )
    with patch("hooks.post_output.subprocess.run") as run:
        run.return_value = MagicMock(stdout=json.dumps(outputs))
        sync_private_dns_outputs(config, dns_input)
    assert run.call_args_list[0].args[0] == [
        "terraform",
        "-chdir=/work/module",
        "apply",
        "-refresh-only",
        "-auto-approve",
        "-input=false",
        "-lock=true",
        "-var-file=/work/module/terraform.tfvars.json",
    ]
    assert run.call_args_list[1].args[0] == [
        "terraform",
        "-chdir=/work/module",
        "output",
        "-json",
    ]
    assert json.loads(Path(config.outputs_file).read_text(encoding="utf-8")) == outputs


def test_refresh_failure_stops_export(
    config: Config, dns_input: AppInterfaceInput
) -> None:
    original = Path(config.outputs_file).read_text(encoding="utf-8")
    with (
        patch(
            "hooks.post_output.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "terraform"),
        ) as run,
        pytest.raises(subprocess.CalledProcessError),
    ):
        sync_private_dns_outputs(config, dns_input)
    assert run.call_count == 1
    assert Path(config.outputs_file).read_text(encoding="utf-8") == original


@pytest.mark.parametrize("value", [None, ""])
def test_missing_after_refresh_fails(
    config: Config, dns_input: AppInterfaceInput, outputs: dict, value: str | None
) -> None:
    original = Path(config.outputs_file).read_text(encoding="utf-8")
    outputs["private_dns_verification_record_value"]["value"] = value
    with (
        patch(
            "hooks.post_output.subprocess.run",
            return_value=MagicMock(stdout=json.dumps(outputs)),
        ),
        pytest.raises(RuntimeError, match="private_dns_verification_record_value"),
    ):
        sync_private_dns_outputs(config, dns_input)
    assert Path(config.outputs_file).read_text(encoding="utf-8") == original
