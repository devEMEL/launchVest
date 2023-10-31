import json
import os

import algokit_utils
from algosdk.transaction import (
    wait_for_confirmation,
    AssetConfigTxn,
    AssetTransferTxn,
)
from algosdk.v2client.algod import AlgodClient
from algokit_utils import get_algod_client, get_algonode_config, Account
from algosdk import mnemonic
from backend.smart_contracts.helpers.asset_helpers.asset_info import asset_holding_info
from backend.smart_contracts.helpers.account_helpers.account import generate_algo_funded_account

from dotenv import load_dotenv


DOTENV_LOCALNET_PATH = "../../../.env.localnet"
DOTENV_TESTNET_PATH = "../../../.env.testnet"

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), DOTENV_TESTNET_PATH))
load_dotenv(dotenv_path)


def create_asset(
    account: Account,
    unit_name: str,
    asset_name: str,
    total: int,
    decimals: int,
    client: AlgodClient
) -> int:
    print("Create Asset")

    txn = AssetConfigTxn(
        sender=account.address,
        sp=client.suggested_params(),
        total=total,
        default_frozen=False,
        unit_name=unit_name,
        asset_name=asset_name,
        url="",
        decimals=decimals,
        strict_empty_address_check=False
    )

    signed_txn = txn.sign(account.private_key)

    try:
        tx_id = client.send_transaction(signed_txn)
        print(f"Transaction ID {tx_id}")
        confirmed_txn = wait_for_confirmation(client, tx_id, 4)
        print(f"Transaction ID {tx_id}")
        print(f"Confirmed transaction in {confirmed_txn['confirmed-round']} rounds")
    except Exception as e:
        print(e)

    print(f"Transaction information {json.dumps(confirmed_txn, indent=4)}")

    try:
        ptx = client.pending_transaction_info(tx_id)
        asset_id = ptx["asset-index"]
        return asset_id
    except Exception as e:
        print(e)


def optin_asset(
    account: Account,
    asset_id: int,
    client: AlgodClient
) -> None:
    print("Receive Asset")
    account_info = client.account_info(account.address)
    holding = None
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx += 1
        if scrutinized_asset['asset-id'] == asset_id:
            holding = True
            break
    if not holding:
        txn = AssetTransferTxn(
            sender=account.address,
            sp=client.suggested_params(),
            receiver=account.address,
            amt=0,
            index=asset_id
        )
        signed_txn = txn.sign(account.private_key)
        try:
            tx_id = client.send_transaction(signed_txn)
            print(f"Signed transaction with TX ID {tx_id}")
            confirmed_txn = wait_for_confirmation(client, tx_id, 4)
            print(f"TX ID {tx_id}")
            print(f"Result confirmed in {confirmed_txn['confirmed-round']} rounds")
        except Exception as e:
            print(e)


def transfer_asset(
    sender: Account,
    receiver: Account | str,
    amt: int,
    asset_id: int,
    client: AlgodClient
) -> None:
    print("Transfer Asset")
    txn = AssetTransferTxn(
        sender=sender.address,
        sp=client.suggested_params(),
        receiver=receiver.address if isinstance(receiver, Account) else receiver,
        amt=amt,
        index=asset_id
    )

    signed_txn = txn.sign(sender.private_key)

    try:
        tx_id = client.send_transaction(signed_txn)
        print(f"Signed transaction with TX ID {tx_id}")

        confirmed_txn = wait_for_confirmation(client, tx_id)
        print(f"TX ID {tx_id}")
        print(f"Result confirmed in {confirmed_txn['confirmed-round']} rounds")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    algod_client = get_algod_client(
        config=algokit_utils.get_algonode_config(network="testnet", config="algod", token="")
    )

    # owner_acct = generate_algo_funded_account(amount=100, client=algod_client)
    owner_acct = Account(private_key=mnemonic.to_private_key(os.getenv("DEPLOYER_MNEMONIC")))
    asset_id = create_asset(
        account=owner_acct,
        unit_name="XEBA",
        asset_name="XEBA",
        total=20_000_000_000_000_000,
        decimals=8,
        client=algod_client
    )
    print(asset_id)
    asset_holding_info(algod_client=algod_client, address=owner_acct.address, asset_id=asset_id)
    acct1 = generate_algo_funded_account(amount=100, client=algod_client)
    optin_asset(account=acct1, asset_id=asset_id, client=algod_client)
    transfer_asset(sender=owner_acct, receiver=acct1, amt=10, asset_id=asset_id, client=algod_client)
    asset_holding_info(algod_client=algod_client, address=acct1.address, asset_id=asset_id)
    asset_holding_info(algod_client=algod_client, address=owner_acct.address, asset_id=asset_id)
