from unittest.mock import MagicMock

import pytest

from hooks_lib.aws_api import ACTIVE_CONNECTION_STATES, AWSApi


@pytest.fixture
def mock_botocore_config(mocker: MagicMock) -> MagicMock:
    return mocker.patch("hooks_lib.aws_api.Config")


@pytest.fixture
def mock_session(mocker: MagicMock) -> MagicMock:
    return mocker.patch("hooks_lib.aws_api.Session")


def test_aws_api_init(mock_session: MagicMock, mock_botocore_config: MagicMock) -> None:
    config_options = {"region_name": "us-east-1"}
    api = AWSApi(config_options=config_options)
    mock_session.assert_called_once_with()
    assert api.session == mock_session.return_value
    mock_botocore_config.assert_called_once_with(**config_options)
    assert api.config == mock_botocore_config.return_value


@pytest.fixture
def aws_api(
    mock_session: MagicMock,
    mocker: MagicMock,
) -> tuple[AWSApi, MagicMock]:
    mocker.patch("hooks_lib.aws_api.Config")
    api = AWSApi(config_options={})
    return api, mock_session.return_value


def test_aws_api_ec2_client(aws_api: tuple[AWSApi, MagicMock]) -> None:
    api, mock_session = aws_api
    client = api.ec2_client
    mock_session.client.assert_called_once_with("ec2", config=api.config)
    assert client == mock_session.client.return_value


@pytest.fixture
def aws_api_with_mock_client(
    aws_api: tuple[AWSApi, MagicMock],
) -> tuple[AWSApi, MagicMock]:
    api, mock_session = aws_api
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client
    return api, mock_client


def test_get_active_endpoint_connections_empty(
    aws_api_with_mock_client: tuple[AWSApi, MagicMock],
) -> None:
    api, mock_client = aws_api_with_mock_client
    paginator = MagicMock()
    mock_client.get_paginator.return_value = paginator
    paginator.paginate.return_value = [{"VpcEndpointConnections": []}]

    result = api.get_active_endpoint_connections("vpce-svc-0123")

    mock_client.get_paginator.assert_called_once_with(
        "describe_vpc_endpoint_connections"
    )
    paginator.paginate.assert_called_once_with(
        Filters=[{"Name": "service-id", "Values": ["vpce-svc-0123"]}]
    )
    assert result == []


def test_get_active_endpoint_connections_filters_by_state(
    aws_api_with_mock_client: tuple[AWSApi, MagicMock],
) -> None:
    api, mock_client = aws_api_with_mock_client
    paginator = MagicMock()
    mock_client.get_paginator.return_value = paginator
    paginator.paginate.return_value = [
        {
            "VpcEndpointConnections": [
                {"VpcEndpointId": "vpce-aaa", "VpcEndpointState": "available"},
                {"VpcEndpointId": "vpce-bbb", "VpcEndpointState": "rejected"},
                {"VpcEndpointId": "vpce-ccc", "VpcEndpointState": "pending"},
                {"VpcEndpointId": "vpce-ddd", "VpcEndpointState": "pending-acceptance"},
                {"VpcEndpointId": "vpce-eee", "VpcEndpointState": "deleted"},
            ]
        }
    ]

    result = api.get_active_endpoint_connections("vpce-svc-0123")

    assert set(result) == {"vpce-aaa", "vpce-ccc", "vpce-ddd"}


def test_active_connection_states_content() -> None:
    assert {"available", "pending", "pending-acceptance"} == ACTIVE_CONNECTION_STATES
