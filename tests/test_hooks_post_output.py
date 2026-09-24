import json
from pathlib import Path
from unittest.mock import patch

import pytest
from external_resources_io.config import Config

from hooks.post_output import VERIFICATION_OUTPUTS, check, main


@pytest.fixture
def outputs() -> dict:
    return {
        "endpoint_service_id": {"value": "vpce-svc-123"},
        "private_dns_verification_record_name": {"value": "_verification"},
        "private_dns_verification_record_type": {"value": "TXT"},
        "private_dns_verification_record_value": {"value": "vpce:verification"},
        "private_dns_verification_state": {"value": "pendingVerification"},
    }


def test_complete_outputs(outputs: dict) -> None:
    assert check(outputs)


@pytest.mark.parametrize("key", VERIFICATION_OUTPUTS)
@pytest.mark.parametrize("value", [None, ""])
def test_empty_output(outputs: dict, key: str, value: str | None) -> None:
    outputs[key]["value"] = value
    assert not check(outputs)


@pytest.mark.parametrize("key", VERIFICATION_OUTPUTS)
def test_missing_output(outputs: dict, key: str) -> None:
    outputs.pop(key)
    assert not check(outputs)


@pytest.mark.parametrize("dns_enabled", [False, True])
@pytest.mark.parametrize("complete", [False, True])
def test_main(
    base_input: dict,
    outputs: dict,
    tmp_path: Path,
    *,
    dns_enabled: bool,
    complete: bool,
) -> None:
    if dns_enabled:
        base_input["data"]["private_dns_name"] = "test.devshift.net"
    output_path = tmp_path / "output.json"
    output_path.write_text(json.dumps(outputs if complete else {}), encoding="utf-8")
    with (
        patch("hooks.post_output.read_input_from_file", return_value=base_input),
        patch(
            "hooks.post_output.Config",
            return_value=Config(OUTPUTS_FILE=str(output_path)),
        ),
    ):
        if dns_enabled and not complete:
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1
        else:
            main()
