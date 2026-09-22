import json
from pathlib import Path

import pytest
from external_resources_io.config import Config

from er_aws_vpc_endpoint_service.input import AppInterfaceInput
from hooks.post_output import VERIFICATION_OUTPUTS, validate_private_dns_outputs


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
def test_skip_validation(
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
    original = Path(config.outputs_file).read_text(encoding="utf-8")
    validate_private_dns_outputs(config, dns_input)
    assert Path(config.outputs_file).read_text(encoding="utf-8") == original


@pytest.mark.parametrize("missing", [None, *VERIFICATION_OUTPUTS])
def test_missing_output_requests_another_run(
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
    original = Path(config.outputs_file).read_text(encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        validate_private_dns_outputs(config, dns_input)
    assert exc.value.code == 1
    assert Path(config.outputs_file).read_text(encoding="utf-8") == original


@pytest.mark.parametrize("key", VERIFICATION_OUTPUTS)
@pytest.mark.parametrize("value", [None, ""])
def test_empty_output_requests_another_run(
    config: Config,
    dns_input: AppInterfaceInput,
    outputs: dict,
    key: str,
    value: str | None,
) -> None:
    outputs[key]["value"] = value
    Path(config.outputs_file).write_text(json.dumps(outputs), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        validate_private_dns_outputs(config, dns_input)
    assert exc.value.code == 1
