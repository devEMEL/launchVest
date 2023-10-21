import logging
import os.path
import shutil
import time
from pathlib import Path

import algokit_utils
from algokit_utils import Account, TransactionParameters
from algosdk import encoding, mnemonic
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import PaymentTxn, SuggestedParams
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv

from backend.smart_contracts.helpers.account_helpers.account import (
    fund_account_with_algos,
    generate_algo_funded_account
)
from backend.smart_contracts.helpers.asset_helpers.asset_manager import (
    transfer_asset,
    optin_asset
)
from backend.smart_contracts.helpers.build import build
from backend.smart_contracts.helpers.date_time_helpers.time_conversion import (
    convert_to_timestamp,
    timestamp_from_log_to_time
)
from backend.smart_contracts.launch_vest.contract import app


ARTIFACTS_PATH = "../artifacts"

DOTENV_LOCALNET_PATH = "../../.env.localnet"
DOTENV_TESTNET_PATH = "../../.env.testnet"

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), DOTENV_TESTNET_PATH))
load_dotenv(dotenv_path)

TESTNET_ASSET_ID = 444276289

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
# noinspection PyArgumentList
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.ApplicationSpecification,
    deployer: algokit_utils.Account,
) -> None:
    from backend.smart_contracts.artifacts.launch_vest.client import (
        LaunchVestClient,
    )

    app_client = LaunchVestClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )
    app_client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )
    app_id = app_client.app_id
    app_addr = app_client.app_address

    # # Bootstrap app
    app_client.bootstrap()

    project_owner_account = Account(private_key=mnemonic.to_private_key(os.getenv("PROJECT_OWNER_MNEMONIC")))
    project_id = project_asset_id = TESTNET_ASSET_ID

    print(f"Deployer: {deployer.address}")
    print(f"Project owner address: {project_owner_account.address}")
    print(f"Escrow address: {app_addr}")

    print(f"Deployer asset holding: {algod_client.account_info(deployer.address)['amount']}")
    print(f"Project owner asset holding: {algod_client.account_info(project_owner_account.address)['amount']}")
    print(f"Escrow address asset holding: {algod_client.account_info(app_addr)['amount']}")

    project_start_timestamp = convert_to_timestamp("2023-10-21 08:01:00")
    project_end_timestamp = convert_to_timestamp("2023-10-21 08:05:00")
    claim_timestamp = convert_to_timestamp("2023-10-21 09:00:00")

    # # List project
    project_owner_client = LaunchVestClient(
        algod_client=algod_client,
        app_id=app_id,
        signer=project_owner_account,
        indexer_client=indexer_client
    )
    txn = project_owner_client.list_project(
        asset_id=project_asset_id,
        start_timestamp=project_start_timestamp,
        end_timestamp=project_end_timestamp,
        claim_timestamp=claim_timestamp,
        asset_price=1,
        min_investment_per_user=1,
        max_investment_per_user=5,
        max_cap=2500,
        total_tokens_for_sale=2500,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )
    try:
        tx_info = txn.tx_info['logs']
        timestamp_from_log_to_time(tx_info[0])
    except KeyError as e:
        raise f"No time log {e}"

    response = project_owner_client.get_project(
        project_id=project_id,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )
    print(response.return_value)

    transfer_asset(sender=project_owner_account, receiver=app_addr, amt=250_000_000_000, asset_id=project_asset_id)

    # # Invest in project
    time.sleep(60)
    investor1_account = Account(private_key=mnemonic.to_private_key(os.getenv("INVESTOR_MNEMONIC")))

    investor1_account_client = LaunchVestClient(
        algod_client,
        app_id=app_id,
        signer=investor1_account.signer,
        indexer_client=indexer_client
    )
    investor1_account_client.invest(
        asset=project_id,
        txn=TransactionWithSigner(
            txn=PaymentTxn(
                sender=investor1_account.address,
                sp=algod_client.suggested_params(),
                receiver=app_addr,
                amt=2
            ),
            signer=investor1_account.signer
        ),
        transaction_parameters=TransactionParameters(
            boxes=[
                (app_id, project_id.to_bytes(8, "big")),
                (app_id, encoding.decode_address(investor1_account.address)),
            ],
        )
    )


def execute_deployment(network: str = "localnet") -> None:
    print(f"Deploying on {network}... 🚀")
    algod_client: AlgodClient
    indexer_client: IndexerClient
    depoyer: Account

    artifacts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ARTIFACTS_PATH))

    if os.path.exists(artifacts_path):
        shutil.rmtree(artifacts_path)
    build(Path(f"{artifacts_path}/{app.name}"), app)

    if network == "localnet":
        algod_client = algokit_utils.get_algod_client()
        indexer_client = algokit_utils.get_indexer_client()
        deployer = generate_algo_funded_account(amount=100, client=algod_client)
    elif network == "testnet":
        algod_client = algokit_utils.get_algod_client(
            config=algokit_utils.get_algonode_config(network="testnet", config="algod", token="")
        )
        indexer_client = algokit_utils.get_indexer_client(
            config=algokit_utils.get_algonode_config(network="testnet", config="indexer", token="")
        )
        deployer = Account(private_key=mnemonic.to_private_key(os.getenv("DEPLOYER_MNEMONIC")))

    deploy(
        algod_client=algod_client,
        indexer_client=indexer_client,
        app_spec=app.build(),
        deployer=deployer
    )


execute_deployment(network="testnet")
