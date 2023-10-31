import os.path
import shutil
import time
from pathlib import Path

import algokit_utils
from algosdk.util import algos_to_microalgos
from algokit_utils import Account, TransactionParameters
from algosdk import encoding, mnemonic
from algosdk.atomic_transaction_composer import TransactionSigner, TransactionWithSigner
from algosdk.transaction import AssetTransferTxn, PaymentTxn, SuggestedParams
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv

from backend.smart_contracts.helpers.formula_helpers import (
    asset_price_with_decimals
)
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
from backend.smart_contracts.launch_vest.contract import app as launch_vest
from backend.smart_contracts.launch_vest.staking import app as vest_stake


ARTIFACTS_PATH = "../artifacts"

DOTENV_LOCALNET_PATH = "../../.env.localnet"
DOTENV_TESTNET_PATH = "../../.env.testnet"

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), DOTENV_TESTNET_PATH))
load_dotenv(dotenv_path)

TESTNET_ASSET_ID_T = 444276289
NEW_TEST_ASSET = 463610258
ASSET_PRICE = 1
ASSET_DECIMAL = 6
# MIN_BUY = 1
MIN_BUY = 900_000
MAX_BUY = 5_000_000


def send_algos(
    sender: Account,
    receiver: Account | str,
    amt: int,
    sp: SuggestedParams
) -> TransactionWithSigner:
    return TransactionWithSigner(
        txn=PaymentTxn(
            sender=sender.address,
            sp=sp,
            receiver=receiver.address if isinstance(receiver, Account) else receiver,
            amt=amt
        ),
        signer=sender.signer
    )


def deposit_ido_assets(
    sender: Account,
    receiver: Account | str,
    amt: int,
    asset_id: int,
    sp: SuggestedParams
) -> TransactionWithSigner:
    return TransactionWithSigner(
        txn=AssetTransferTxn(
            sender=sender.address,
            sp=sp,
            receiver=receiver.address if isinstance(receiver, Account) else receiver,
            amt=amt,
            index=asset_id
        ),
        signer=sender.signer
    )


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

    # Fund escrow account
    if algod_client.account_info(app_addr)['amount'] == 0:
        app_client.fund_escrow_address(
            txn=send_algos(
                sender=deployer,
                receiver=app_addr,
                amt=algos_to_microalgos(2),
                sp=algod_client.suggested_params()
            )
        )

    project_owner_account = Account(private_key=mnemonic.to_private_key(os.getenv("PROJECT_OWNER_MNEMONIC")))
    project_id = project_asset_id = TESTNET_ASSET_ID_T

    print(f"Deployer: {deployer.address}")
    print(f"Project owner address: {project_owner_account.address}")
    print(f"Escrow address: {app_addr}")

    print(f"Deployer Algo holding: {algod_client.account_info(deployer.address)['amount']}")
    print(f"Project owner Algo holding: {algod_client.account_info(project_owner_account.address)['amount']}")
    print(f"Escrow address Algo holding: {algod_client.account_info(app_addr)['amount']}")

    current_time = int(time.time())
    print(f"Current local timestamp: {current_time}")
    project_start_timestamp = current_time - 30  # Subtracting 40sec. so my time can match the
    # pt.Global.latest_timestamp()
    project_end_timestamp = project_start_timestamp + 40
    claim_timestamp = project_end_timestamp + 20

    # # List project
    project_owner_client = LaunchVestClient(
        algod_client=algod_client,
        app_id=app_id,
        signer=project_owner_account,
        indexer_client=indexer_client
    )

    project_owner_client.list_project(
        asset_id=project_asset_id,
        image_url="",
        start_timestamp=project_start_timestamp,
        end_timestamp=project_end_timestamp,
        claim_timestamp=claim_timestamp,
        price_per_asset=int(asset_price_with_decimals(ASSET_PRICE, ASSET_DECIMAL)),
        min_investment_per_investor=MIN_BUY,
        max_investment_per_investor=MAX_BUY,
        vesting_schedule=7_776_000,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )

    response = project_owner_client.get_project(
        project_id=project_id,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )
    print(response.return_value)

    # Deposit IDO tokens
    project_owner_client.deposit_ido_assets(
        txn=deposit_ido_assets(
            sender=project_owner_account,
            receiver=app_addr,
            amt=int(asset_price_with_decimals(ASSET_PRICE, ASSET_DECIMAL)),
            asset_id=project_asset_id,
            sp=algod_client.suggested_params()
        ),
        asset=project_asset_id,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )

    response = project_owner_client.get_project(
        project_id=project_id,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )
    print(response.return_value)

    # Invest in project
    time.sleep(15)
    investor1_account = Account(private_key=mnemonic.to_private_key(os.getenv("INVESTOR_MNEMONIC")))

    investor1_account_client = LaunchVestClient(
        algod_client,
        app_id=app_id,
        signer=investor1_account.signer,
        indexer_client=indexer_client
    )
    investor1_account_client.invest(
        is_staking=True,
        project=project_id,
        txn=TransactionWithSigner(
            txn=PaymentTxn(
                sender=investor1_account.address,
                sp=algod_client.suggested_params(),
                receiver=app_addr,
                amt=MIN_BUY
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

    response = investor1_account_client.get_investor(
        investor=investor1_account.address,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, encoding.decode_address(investor1_account.address))]
        )
    )
    print(response.return_value)

    response = project_owner_client.get_project(
        project_id=project_id,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )
    print(response.return_value)

    time.sleep(70)
    investor1_account_client.claim_ido_asset(
        is_staking=True,
        project=project_asset_id,
        transaction_parameters=TransactionParameters(
            boxes=[
                (app_id, project_id.to_bytes(8, "big")),
                (app_id, encoding.decode_address(investor1_account.address)),
            ]
        )
    )
    response = investor1_account_client.get_investor(
        investor=investor1_account.address,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, encoding.decode_address(investor1_account.address))]
        )
    )
    print(response.return_value)

    project_owner_client.withdraw_amount_raised(
        project_id=project_id,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )

    response = project_owner_client.get_project(
        project_id=project_id,
        transaction_parameters=TransactionParameters(
            boxes=[(app_id, project_id.to_bytes(8, "big"))]
        )
    )
    print(response.return_value)

    # project_owner_client.list_project(
    #     asset_id=project_asset_id,
    #     start_timestamp=project_start_timestamp,
    #     end_timestamp=project_end_timestamp,
    #     claim_timestamp=claim_timestamp,
    #     price_per_asset=int(asset_price_with_decimals(ASSET_PRICE, ASSET_DECIMAL)),
    #     min_investment_per_investor=algos_to_microalgos(MIN_BUY),
    #     max_investment_per_investor=algos_to_microalgos(MAX_BUY),
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    #
    # response = project_owner_client.get_project(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Deposit IDO tokens
    # project_owner_client.deposit_ido_assets(
    #     txn=deposit_ido_assets(
    #         sender=project_owner_account,
    #         receiver=app_addr,
    #         amt=int(asset_price_with_decimals(ASSET_PRICE, ASSET_DECIMAL)),
    #         asset_id=project_asset_id,
    #         sp=algod_client.suggested_params()
    #     ),
    #     asset=project_asset_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    #
    # response = project_owner_client.get_project(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Invest in project
    # time.sleep(15)
    # investor1_account = Account(private_key=mnemonic.to_private_key(os.getenv("INVESTOR_MNEMONIC")))
    #
    # investor1_account_client = LaunchVestClient(
    #     algod_client,
    #     app_id=app_id,
    #     signer=investor1_account.signer,
    #     indexer_client=indexer_client
    # )
    # investor1_account_client.invest(
    #     project=project_id,
    #     txn=TransactionWithSigner(
    #         txn=PaymentTxn(
    #             sender=investor1_account.address,
    #             sp=algod_client.suggested_params(),
    #             receiver=app_addr,
    #             amt=algos_to_microalgos(MIN_BUY)
    #         ),
    #         signer=investor1_account.signer
    #     ),
    #     transaction_parameters=TransactionParameters(
    #         boxes=[
    #             (app_id, project_id.to_bytes(8, "big")),
    #             (app_id, encoding.decode_address(investor1_account.address)),
    #         ],
    #     )
    # )
    #
    # response = investor1_account_client.get_investor(
    #     investor=investor1_account.address,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, encoding.decode_address(investor1_account.address))]
    #     )
    # )
    # print(response.return_value)
    #
    # response = project_owner_client.get_project(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Claim asset
    # time.sleep(60)
    # investor1_account_client.claim_project_asset(
    #     project=project_asset_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[
    #             (app_id, project_id.to_bytes(8, "big")),
    #             (app_id, encoding.decode_address(investor1_account.address)),
    #         ]
    #     )
    # )
    # response = investor1_account_client.get_investor(
    #     investor=investor1_account.address,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, encoding.decode_address(investor1_account.address))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Withdraw funds
    # time.sleep(120)
    # project_owner_client.withdraw_amount_raised(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    #
    # response = project_owner_client.get_project(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Second transaction
    # project_owner_account_2 = Account(private_key=mnemonic.to_private_key(os.getenv("PROJECT_OWNER_MNEMONIC_2")))
    # project_id = project_asset_id = TESTNET_ASSET_ID_Z
    #
    # print(f"Project owner address: {project_owner_account_2.address}")
    # print(f"Escrow address: {app_addr}")
    #
    # print(f"Deployer Algo holding: {algod_client.account_info(deployer.address)['amount']}")
    # print(f"Project owner Algo holding: {algod_client.account_info(project_owner_account_2.address)['amount']}")
    # print(f"Escrow address Algo holding: {algod_client.account_info(app_addr)['amount']}")
    #
    # current_time = int(time.time())
    # print(f"Current local timestamp: {current_time}")
    # project_start_timestamp = current_time + 5
    # project_end_timestamp = project_start_timestamp + 30
    # claim_timestamp = project_end_timestamp + 50
    #
    # # # List project
    # project_owner_client = LaunchVestClient(
    #     algod_client=algod_client,
    #     app_id=app_id,
    #     signer=project_owner_account_2,
    #     indexer_client=indexer_client
    # )
    # project_owner_client.list_project(
    #     asset_id=project_asset_id,
    #     start_timestamp=project_start_timestamp,
    #     end_timestamp=project_end_timestamp,
    #     claim_timestamp=claim_timestamp,
    #     price_per_asset=int(asset_price_with_decimals(ASSET_PRICE, ASSET_DECIMAL)),
    #     min_investment_per_investor=algos_to_microalgos(MIN_BUY),
    #     max_investment_per_investor=algos_to_microalgos(MAX_BUY),
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    #
    # response = project_owner_client.get_project(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Deposit IDO tokens
    # project_owner_client.deposit_ido_assets(
    #     txn=deposit_ido_assets(
    #         sender=project_owner_account_2,
    #         receiver=app_addr,
    #         amt=int(asset_price_with_decimals(ASSET_PRICE, ASSET_DECIMAL)),
    #         asset_id=project_asset_id,
    #         sp=algod_client.suggested_params()
    #     ),
    #     asset=project_asset_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    #
    # response = project_owner_client.get_project(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Invest in project
    # time.sleep(15)
    # investor1_account = Account(private_key=mnemonic.to_private_key(os.getenv("INVESTOR_MNEMONIC")))
    #
    # investor1_account_client = LaunchVestClient(
    #     algod_client,
    #     app_id=app_id,
    #     signer=investor1_account.signer,
    #     indexer_client=indexer_client
    # )
    # investor1_account_client.invest(
    #     project=project_id,
    #     txn=TransactionWithSigner(
    #         txn=PaymentTxn(
    #             sender=investor1_account.address,
    #             sp=algod_client.suggested_params(),
    #             receiver=app_addr,
    #             amt=algos_to_microalgos(MIN_BUY)
    #         ),
    #         signer=investor1_account.signer
    #     ),
    #     transaction_parameters=TransactionParameters(
    #         boxes=[
    #             (app_id, project_id.to_bytes(8, "big")),
    #             (app_id, encoding.decode_address(investor1_account.address)),
    #         ],
    #     )
    # )
    #
    # response = investor1_account_client.get_investor(
    #     investor=investor1_account.address,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, encoding.decode_address(investor1_account.address))]
    #     )
    # )
    # print(response.return_value)
    #
    # response = project_owner_client.get_project(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Claim asset
    # time.sleep(60)
    # investor1_account_client.claim_project_asset(
    #     project=project_asset_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[
    #             (app_id, project_id.to_bytes(8, "big")),
    #             (app_id, encoding.decode_address(investor1_account.address)),
    #         ]
    #     )
    # )
    # response = investor1_account_client.get_investor(
    #     investor=investor1_account.address,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, encoding.decode_address(investor1_account.address))]
    #     )
    # )
    # print(response.return_value)
    #
    # # # Withdraw funds
    # time.sleep(120)
    # project_owner_client.withdraw_amount_raised(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    #
    # response = project_owner_client.get_project(
    #     project_id=project_id,
    #     transaction_parameters=TransactionParameters(
    #         boxes=[(app_id, project_id.to_bytes(8, "big"))]
    #     )
    # )
    # print(response.return_value)


def execute_deployment(network: str = "localnet") -> None:
    print(f"Deploying on {network}... 🚀")
    algod_client: AlgodClient
    indexer_client: IndexerClient
    depoyer: Account

    artifacts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ARTIFACTS_PATH))

    if os.path.exists(artifacts_path):
        shutil.rmtree(artifacts_path)
    # build(Path(f"{artifacts_path}/{vest_stake.name}"), vest_stake)
    build(Path(f"{artifacts_path}/{launch_vest.name}"), launch_vest)

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

    # deploy(
    #     algod_client=algod_client,
    #     indexer_client=indexer_client,
    #     app_spec=vest_stake.build(),
    #     deployer=deployer
    # )
    deploy(
        algod_client=algod_client,
        indexer_client=indexer_client,
        app_spec=launch_vest.build(),
        deployer=deployer
    )


execute_deployment(network="testnet")
