#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys

from external_resources_io.config import Config
from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.log import setup_logging
from external_resources_io.terraform import (
    Action,
    TerraformJsonPlanParser,
)

from er_aws_vpc_endpoint_service.input import AppInterfaceInput
from hooks_lib.aws_api import AWSApi

logger = logging.getLogger(__name__)


class VpcEndpointServicePlanValidator:
    """Validate the Terraform plan for VPC Endpoint Service changes."""

    def __init__(
        self,
        plan: TerraformJsonPlanParser,
        app_interface_input: AppInterfaceInput,
    ) -> None:
        self.plan = plan
        self.input = app_interface_input
        self.aws_api = AWSApi(config_options={"region_name": self.input.data.region})
        self.errors: list[str] = []

    def validate(self) -> bool:
        """Check for active connections before deletion; return True if no errors."""
        for change in self.plan.plan.resource_changes:
            if change.type != "aws_vpc_endpoint_service":
                continue
            if not (change.change and Action.ActionDelete in change.change.actions):
                continue

            before = change.change.before or {}
            service_id = before.get("id", "")

            if not service_id:
                self.errors.append(
                    f"Cannot determine service ID for '{change.address}'. "
                    "Refusing to proceed with deletion."
                )
                continue

            active = self.aws_api.get_active_endpoint_connections(service_id)
            if active:
                self.errors.append(
                    f"VPC Endpoint Service '{change.address}' ({service_id}) has "
                    f"{len(active)} active connection(s): {', '.join(active)}. "
                    "Remove all VPC Endpoints before deleting the service."
                )

        return not self.errors


if __name__ == "__main__":
    setup_logging()
    app_interface_input = parse_model(AppInterfaceInput, read_input_from_file())
    plan = TerraformJsonPlanParser(plan_path=Config().plan_file_json)
    validator = VpcEndpointServicePlanValidator(plan, app_interface_input)
    if not validator.validate():
        logger.error(validator.errors)
        sys.exit(1)
    logger.info("Validation ended successfully")
