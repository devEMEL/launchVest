import algokit_utils
from algokit_utils import EnsureBalanceParameters
from algosdk.util import algos_to_microalgos
from algosdk.v2client.algod import AlgodClient


def fund_account_with_algos(
    client: AlgodClient,
    account: algokit_utils.Account | str,
    min_spending_balance: int,
    min_fund_increment: int = 0,
) -> None:
    algokit_utils.ensure_funded(
        client=client,
        parameters=EnsureBalanceParameters(
            account_to_fund=account,
            min_spending_balance_micro_algos=algos_to_microalgos(min_spending_balance),
            min_funding_increment_micro_algos=algos_to_microalgos(min_fund_increment),
        )
    )


def generate_account() -> algokit_utils.Account:
    return algokit_utils.Account.new_account()


def generate_algo_funded_account(
    amount: int,
    client: AlgodClient,
) -> algokit_utils.Account:
    generated_account = generate_account()
    fund_account_with_algos(
        client=client,
        account=generated_account,
        min_spending_balance=amount
    )
    return generated_account
