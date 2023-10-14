import pytest
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    get_localnet_default_account,
)
from algosdk.v2client.algod import AlgodClient

from smart_contracts.launch_vest import contract as launch_vest_contract


@pytest.fixture(scope="session")
def launch_vest_app_spec(algod_client: AlgodClient) -> ApplicationSpecification:
    return launch_vest_contract.app.build(algod_client)


@pytest.fixture(scope="session")
def launch_vest_client(
    algod_client: AlgodClient, launch_vest_app_spec: ApplicationSpecification
) -> ApplicationClient:
    client = ApplicationClient(
        algod_client,
        app_spec=launch_vest_app_spec,
        signer=get_localnet_default_account(algod_client),
    )
    client.create()
    return client


def test_says_hello(launch_vest_client: ApplicationClient) -> None:
    result = launch_vest_client.call(launch_vest_contract.hello, name="World")

    assert result.return_value == "Hello, World"
