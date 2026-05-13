# External Resources VPC Endpoint Service Module

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

External Resources module to provision and manage AWS VPC Endpoint Services (AWS PrivateLink — provider side) with app-interface.

Wraps an existing Network Load Balancer (NLB) provisioned by an OpenShift Service of type `LoadBalancer` into an AWS VPC Endpoint Service, enabling other accounts and clusters to connect via PrivateLink.

## Resources Managed

| Resource | Terraform Type | Notes |
|---|---|---|
| VPC Endpoint Service | `aws_vpc_endpoint_service` | Attached to the NLB discovered by the OpenShift Service tag. |

## Design Decisions

- **One endpoint service per module invocation** — matches the ERv2 pattern of one resource per invocation.
- **NLB is pre-existing** — not managed by this module. It is discovered automatically via the `kubernetes.io/service-name` tag set by the OpenShift cloud controller.
- **NLB namespace is implicit** — the ERv2 resource must be provisioned in the same namespace as the OpenShift Service that created the NLB. The namespace is derived from `provision.target_namespace`.
- **`acceptance_required` is hardcoded to `false`** — connections from allowed principals are accepted automatically.
- **Allowed principals are IAM root ARNs** — derived from the AWS account UID of each consumer cluster. Grants access to all IAM identities in that account.
- **IPv4 only** — `supported_ip_address_types` is hardcoded to `["ipv4"]`.

## Tech stack

* Terraform
* AWS provider
* Python 3.12
* Pydantic

## Development

Prepare your local development environment:

```bash
make dev
```

See the `Makefile` for more details.

### Update Terraform providers

To update the Terraform providers used in this project, bump the version in [versions.tf](/terraform/versions.tf) and update the Terraform lockfile via:

```bash
make providers-lock
```

### Development workflow

1. Make changes to the code.
1. Build the image with `make build`.
1. Run the image manually with a proper input file and credentials. See the [Debugging](#debugging) section below.
1. Please don't forget to remove (`-e ACTION=Destroy`) any development AWS resources you create, as they will incur costs.

## Debugging

To debug and run the module locally, run the following commands:

```bash
# Get the input file from app-interface
$ qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider vpc-endpoint-service --identifier <IDENTIFIER> get-input > tmp/input.json

# Get the AWS credentials
$ qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider vpc-endpoint-service --identifier <IDENTIFIER> get-credentials > tmp/credentials

# Run the module
$ podman run --rm -it \
    --mount type=bind,source=$PWD/tmp/input.json,target=/inputs/input.json \
    --mount type=bind,source=$PWD/tmp/credentials,target=/credentials \
    --mount type=bind,source=$PWD/tmp/work,target=/work \
    -e DRY_RUN=True \
    -e ACTION=Apply \
    quay.io/redhat-services-prod/app-sre-tenant/er-aws-vpc-endpoint-service-main/er-aws-vpc-endpoint-service-main:latest
```

## Known Limitations

- **NLB namespace coupling** — the OpenShift Service (and its NLB) must live in the same namespace as the ERv2 resource. Cross-namespace discovery is not supported.
- **NLB lifecycle lock** — AWS prevents deletion of an NLB while a VPC Endpoint Service references it. The OpenShift Service cannot be removed until the VPC Endpoint Service is destroyed first.
- **Active connections block deletion** — the post-plan hook prevents `terraform apply` if the service has active VPC Endpoint connections. All consumer endpoints must be destroyed before the service can be deleted.
- **IPv4 only** — dual-stack (IPv6) endpoints are not supported by this module.
