from __future__ import annotations

from typing import Any

from external_resources_io.input import AppInterfaceProvision  # noqa: TC002
from pydantic import BaseModel, Field


class VpcEndpointServiceData(BaseModel):
    """App-Interface input parameters for the VPC Endpoint Service module"""

    region: str
    identifier: str
    openshift_service_name: str
    allowed_principal_arns: list[str] = Field(default_factory=list)
    tags: dict[str, Any] = Field(default_factory=dict)
    output_resource_name: str | None = None


class AppInterfaceInput(BaseModel):
    """Validated app-interface input for the VPC Endpoint Service module."""

    data: VpcEndpointServiceData
    provision: AppInterfaceProvision
