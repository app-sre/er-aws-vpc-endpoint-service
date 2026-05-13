from __future__ import annotations

from typing import TYPE_CHECKING, Any

from boto3 import Session
from botocore.config import Config

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mypy_boto3_ec2 import EC2Client

# States that indicate an endpoint is actively using the service
ACTIVE_CONNECTION_STATES = {"available", "pending", "pending-acceptance"}


class AWSApi:
    """AWS API client for VPC Endpoint Service operations"""

    def __init__(self, config_options: Mapping[str, Any]) -> None:
        self.session = Session()
        self.config = Config(**config_options)

    @property
    def ec2_client(self) -> EC2Client:
        """Return an EC2 client for the configured region."""
        return self.session.client("ec2", config=self.config)

    def get_active_endpoint_connections(self, service_id: str) -> list[str]:
        """Return endpoint IDs with active connections to the given endpoint service."""
        paginator = self.ec2_client.get_paginator("describe_vpc_endpoint_connections")
        endpoint_ids: list[str] = []
        for page in paginator.paginate(
            Filters=[{"Name": "service-id", "Values": [service_id]}]
        ):
            endpoint_ids.extend(
                conn["VpcEndpointId"]
                for conn in page.get("VpcEndpointConnections", [])
                if conn["VpcEndpointState"] in ACTIVE_CONNECTION_STATES
            )
        return endpoint_ids
