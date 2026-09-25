#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from external_resources_io.config import Action, Config
from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.log import setup_logging
from external_resources_io.terraform import TerraformJsonPlanParser

from er_aws_vpc_endpoint_service.input import AppInterfaceInput
from hooks_lib.aws_api import AWSApi

logger = logging.getLogger(__name__)


class VpcEndpointServicePostApply:
    """Run actions after applying the VPC Endpoint Service."""

    def __init__(self, config: Config, ai_input: AppInterfaceInput) -> None:
        self.config = config
        self.input = ai_input

    def remove_private_dns_name(self) -> None:
        """Remove a private DNS name omitted from the input.

        AWS provider 6.47.0 retains an omitted Optional+Computed
        private_dns_name, so Terraform plans no removal (APPSRE-15332).
        """
        if self.input.data.private_dns_name:
            return

        if self.config.dry_run:
            plan = TerraformJsonPlanParser(plan_path=self.config.plan_file_json).plan
            outputs = (plan.planned_values or {}).get("outputs") or {}
        else:
            outputs = json.loads(
                Path(self.config.outputs_file).read_text(encoding="utf-8")
            )
        service_id = outputs.get("endpoint_service_id", {}).get("value")
        if not service_id:
            return

        ec2 = AWSApi(config_options={"region_name": self.input.data.region}).ec2_client
        response = ec2.describe_vpc_endpoint_service_configurations(
            ServiceIds=[service_id]
        )
        configurations = response.get("ServiceConfigurations", [])
        if not configurations:
            raise RuntimeError(f"VPC Endpoint Service {service_id} was not found")
        private_dns_name = configurations[0].get("PrivateDnsName")
        if not private_dns_name:
            return

        if self.config.dry_run:
            logger.info(
                "Would remove private DNS name %s from VPC Endpoint Service %s",
                private_dns_name,
                service_id,
            )
            return

        ec2.modify_vpc_endpoint_service_configuration(
            ServiceId=service_id, RemovePrivateDnsName=True
        )
        logger.info(
            "Removed private DNS name %s from VPC Endpoint Service %s",
            private_dns_name,
            service_id,
        )
        sys.exit(1)


def main() -> None:
    """Run post-apply actions for an apply."""
    config = Config()
    if config.action != Action.APPLY:
        return

    ai_input = parse_model(AppInterfaceInput, read_input_from_file())
    post_apply = VpcEndpointServicePostApply(config, ai_input)
    post_apply.remove_private_dns_name()


if __name__ == "__main__":
    setup_logging()
    main()
