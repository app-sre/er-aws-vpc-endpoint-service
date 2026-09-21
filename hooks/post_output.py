#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import shlex
import subprocess  # ruff: ignore[suspicious-subprocess-import] - Terraform is invoked without a shell
from pathlib import Path

from external_resources_io.config import Action, Config
from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.log import setup_logging

from er_aws_vpc_endpoint_service.input import AppInterfaceInput

logger = logging.getLogger(__name__)

VERIFICATION_OUTPUTS = (
    "private_dns_verification_record_name",
    "private_dns_verification_record_type",
    "private_dns_verification_record_value",
    "private_dns_verification_state",
)


def sync_private_dns_outputs(config: Config, ai_input: AppInterfaceInput) -> None:
    """Recover verification outputs omitted when enabling Private DNS."""
    if (
        config.dry_run
        or config.action != Action.APPLY
        or not ai_input.data.private_dns_name
    ):
        return

    output_path = Path(config.outputs_file)
    outputs = json.loads(output_path.read_text(encoding="utf-8"))
    if all(outputs.get(key, {}).get("value") for key in VERIFICATION_OUTPUTS):
        return

    logger.info(
        "Refreshing Terraform state to recover Private DNS verification outputs"
    )
    command = shlex.split(config.terraform_cmd)
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - command comes from the Terraform runner, not resource input
        [
            *command,
            "apply",
            "-refresh-only",
            "-auto-approve",
            "-input=false",
            "-lock=true",
            f"-var-file={config.tf_vars_file}",
        ],
        check=True,
    )
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - command comes from the Terraform runner
        [*command, "output", "-json"],
        check=True,
        capture_output=True,
        text=True,
    )
    outputs = json.loads(result.stdout)
    missing = [
        key for key in VERIFICATION_OUTPUTS if not outputs.get(key, {}).get("value")
    ]
    if missing:
        raise RuntimeError(
            f"Private DNS verification outputs missing after refresh: {missing}"
        )
    output_path.write_text(result.stdout, encoding="utf-8")


if __name__ == "__main__":
    setup_logging()
    sync_private_dns_outputs(
        Config(), parse_model(AppInterfaceInput, read_input_from_file())
    )
