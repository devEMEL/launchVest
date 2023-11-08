import os
import algokit_utils

from beaker import client
from backend.smart_contracts.vest_stake.contract import app, bootstrap, fund_escrow_address, get_staker, stake
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import AssetTransferTxn, PaymentTxn, SuggestedParams
from algosdk import encoding, mnemonic
from algosdk.util import algos_to_microalgos
from algokit_utils import Account
from dotenv import load_dotenv

DOTENV_TESTNET_PATH = "../../.env.testnet"

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), DOTENV_TESTNET_PATH))
load_dotenv(dotenv_path)

admin_acct = Account(private_key=mnemonic.to_private_key(os.getenv("DEPLOYER_MNEMONIC")))

algod_client = algokit_utils.get_algod_client(
    config=algokit_utils.get_algonode_config(network="testnet", config="algod", token="")
)

VEST_AID = 460043736
FIVE_MINS_STAKING_PERIOD = 300
STAKE_AMOUNT = 80_000_000

app_client = client.ApplicationClient(
    client=algod_client,
    app=app,
    sender=admin_acct.address,
    signer=admin_acct.signer,
)
app_id, app_addr, _ = app_client.create()


print(f"App addr: {app_addr}")
print(f"Deployer addr: {admin_acct.address}")


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


app_client.call(
    fund_escrow_address,
    txn=send_algos(
        sender=admin_acct,
        receiver=app_addr,
        amt=algos_to_microalgos(2),
        sp=algod_client.suggested_params()
    )
)

app_client.call(
    bootstrap,
    asset=VEST_AID
)

# app_client.call(
#     set_stake_amounts,
#     min_stake=5,
#     max_stake=10
# )
#
# app_client.call(
#     set_annual_rate,
#     new_annual_rate=10
# )

txn = TransactionWithSigner(
    txn=AssetTransferTxn(
        sender=admin_acct.address,
        receiver=app_addr,
        amt=200_000_000_00,
        index=VEST_AID,
        sp=algod_client.suggested_params()
    ),
    signer=admin_acct.signer
)

stake_txn = app_client.call(
    stake,
    asset=VEST_AID,
    stake_duration=FIVE_MINS_STAKING_PERIOD,
    txn=txn,
    boxes=[(app_id, encoding.decode_address(admin_acct.address))]
)
# tx_info = stake_txn.tx_info['logs']
# for info in tx_info:
#     print(info)

result = app_client.call(
    get_staker,
    staker=admin_acct.address,
    boxes=[(app_id, encoding.decode_address(admin_acct.address))]
)
print(result.return_value)
#
# app_client.call(
#     stake,
#     asset=VEST_AID,
#     stake_duration=FIVE_MINS_STAKING_PERIOD,
#     txn=txn,
#     boxes=[(app_id, encoding.decode_address(admin_acct.address))]
# )
#
# result = app_client.call(
#     get_staker,
#     staker=admin_acct.address,
#     boxes=[(app_id, encoding.decode_address(admin_acct.address))]
# )
# print(result.return_value)
