from __future__ import annotations

from typing import Any

from external_resources_io.input import AppInterfaceProvision  # noqa: TC002
from pydantic import BaseModel, Field, computed_field


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


class TerraformModuleData(BaseModel):
    """Variables to feed to the Terraform module"""

    ai_input: AppInterfaceInput = Field(exclude=True)

    @computed_field
    def region(self) -> str:
        """Region"""
        return self.ai_input.data.region

    @computed_field
    def identifier(self) -> str:
        """Identifier"""
        return self.ai_input.data.identifier

    @computed_field
    def openshift_service_name(self) -> str:
        """OpenShift service name"""
        return self.ai_input.data.openshift_service_name

    @computed_field
    def allowed_principal_arns(self) -> list[str]:
        """Allowed principal ARNs"""
        return self.ai_input.data.allowed_principal_arns

    @computed_field
    def tags(self) -> dict[str, Any]:
        """Tags"""
        return self.ai_input.data.tags

    @computed_field
    def output_resource_name(self) -> str | None:
        """Output resource name"""
        return self.ai_input.data.output_resource_name

    @computed_field
    def provision(self) -> AppInterfaceProvision:
        """Provision"""
        return self.ai_input.provision
