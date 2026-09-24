#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from external_resources_io.config import Config
from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.log import setup_logging

from er_aws_vpc_endpoint_service.input import AppInterfaceInput

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

VERIFICATION_OUTPUTS = (
    "private_dns_verification_record_name",
    "private_dns_verification_record_type",
    "private_dns_verification_record_value",
    "private_dns_verification_state",
)


def check(outputs: Mapping) -> bool:
    """Check that Private DNS verification outputs are populated."""
    for key in VERIFICATION_OUTPUTS:
        if not outputs.get(key, {}).get("value"):
            logger.error("%s output not found.", key)
            return False
    return True


def main() -> None:
    """Check outputs when Private DNS is configured."""
    ai_input = parse_model(AppInterfaceInput, read_input_from_file())
    if not ai_input.data.private_dns_name:
        return
    output_json = Path(Config().outputs_file)
    if not check(json.loads(output_json.read_text(encoding="utf-8"))):
        sys.exit(1)


if __name__ == "__main__":
    setup_logging()
    main()
