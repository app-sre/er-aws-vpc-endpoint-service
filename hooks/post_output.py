#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import sys
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


def validate_private_dns_outputs(config: Config, ai_input: AppInterfaceInput) -> None:
    """Require verification outputs before allowing secret synchronization."""
    if (
        config.dry_run
        or config.action != Action.APPLY
        or not ai_input.data.private_dns_name
    ):
        return

    output_path = Path(config.outputs_file)
    outputs = json.loads(output_path.read_text(encoding="utf-8"))
    missing = [
        key for key in VERIFICATION_OUTPUTS if not outputs.get(key, {}).get("value")
    ]
    if missing:
        logger.error(
            "Private DNS verification outputs missing: %s. "
            "Failing the job so external-resources schedules another apply.",
            ", ".join(missing),
        )
        sys.exit(1)


if __name__ == "__main__":
    setup_logging()
    validate_private_dns_outputs(
        Config(), parse_model(AppInterfaceInput, read_input_from_file())
    )
