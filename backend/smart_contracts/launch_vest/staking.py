import beaker as bk
import pyteal as pt

from beaker.consts import FALSE, TRUE
from beaker.lib.storage import BoxMapping


FIVE_MINS_STAKING_PERIOD = pt.Int(300)
QUARTER_STAKING_PERIOD = pt.Int(7_884_000)
HALF_YEAR_STAKING_PERIOD = pt.Int(15_768_000)
ANNUAL_STAKING_PERIOD = pt.Int(31_536_000)

SECONDS_IN_A_YEAR = pt.Int(31_536_000)


class Staker(pt.abi.NamedTuple):
    address: pt.abi.Field[pt.abi.Address]
    amount: pt.abi.Field[pt.abi.Uint64]
    asset_id: pt.abi.Field[pt.abi.Uint64]
    is_staking: pt.abi.Field[pt.abi.Bool]
    start_timestamp: pt.abi.Field[pt.abi.Uint64]
    end_timestamp: pt.abi.Field[pt.abi.Uint64]


class State:
    admin_acct = bk.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        default=pt.Bytes("")
    )
    asset_id = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64
    ),
    escrow_address = bk.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        default=pt.Bytes("")
    )
    min_stake = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(100)
    )
    max_stake = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(20_000)
    )
    annual_rate = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(10)
    )
    staker_to_stake = BoxMapping(
        key_type=pt.abi.Address,
        value_type=Staker
    )


app = bk.Application(name="vest_stake", state=State())


# noinspection PyTypeChecker
def calculate_stake_reward(
    stake_amount: pt.abi.Uint64,
    stake_duration: pt.abi.Uint64,
    *,
    output: pt.abi.Uint64
) -> pt.Expr:
    return output.set(
        (stake_amount.get() * app.state.annual_rate * stake_duration.get()) / (pt.Int(100) * SECONDS_IN_A_YEAR)
    )


# noinspection PyTypeChecker
@app.external
def bootstrap(
    asset: pt.abi.Asset
) -> pt.Expr:
    return pt.Seq(
        app.initialize_global_state(),
        app.state.admin_acct.set(pt.Global.creator_address()),
        app.state.escrow_address.set(pt.Global.current_application_address()),
        (escrow_asset_bal := pt.AssetHolding.balance(app.state.escrow_address, asset.asset_id())),
        pt.If(escrow_asset_bal.value() == pt.Int(0), escrow_asset_opt_in(asset=asset)),
    )


def escrow_asset_opt_in(asset: pt.abi.Asset) -> pt.Expr:
    return pt.Seq(
        pt.InnerTxnBuilder.Execute({
            pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
            pt.TxnField.xfer_asset: asset.asset_id(),
            pt.TxnField.asset_amount: pt.Int(0),
            pt.TxnField.asset_receiver: app.state.escrow_address
        })
    )


# noinspection PyTypeChecker
@app.external
def fund_escrow_address(
    txn: pt.abi.PaymentTransaction
) -> pt.Expr:
    """
    Fund escrow address with Algos.

   :param pt.abi.PaymentTransaction txn: The payment transaction to fund the escrow address.
   :rtype: pt.Expr
    """
    return pt.Seq(
        pt.Assert(
            txn.get().amount() > pt.Int(0),
            txn.get().receiver() == pt.Global.current_application_address(),
            txn.get().type_enum() == pt.TxnType.Payment,
        )
    )


# noinspection PyTypeChecker
@app.external(authorize=bk.Authorize.only_creator())
def set_stake_amounts(
    min_stake: pt.abi.Uint64,
    max_stake: pt.abi.Uint64
) -> pt.Expr:
    return pt.Seq(
        pt.Assert(
            min_stake.get() > pt.Int(0),
            max_stake.get() > pt.Int(0),
            max_stake.get() > min_stake.get()
        ),
        app.state.min_stake.set(min_stake.get()),
        app.state.max_stake.set(max_stake.get())
    )


@app.external(authorize=bk.Authorize.only_creator())
def set_annual_rate(new_annual_rate: pt.abi.Uint64) -> pt.Expr:
    return app.state.annual_rate.set(new_annual_rate.get())


# noinspection PyTypeChecker
@app.external
def stake(
    asset: pt.abi.Asset,
    stake_duration: pt.abi.Uint64,
    txn: pt.abi.AssetTransferTransaction
) -> pt.Expr:
    staker = Staker()
    return pt.Seq(
        pt.Assert(
            txn.get().type_enum() == pt.TxnType.AssetTransfer,
            txn.get().asset_receiver() == app.state.escrow_address,
            txn.get().xfer_asset() == asset.asset_id()
        ),
        pt.Assert(
            pt.Or(
                txn.get().asset_amount() > app.state.min_stake,
                txn.get().asset_amount() <= app.state.max_stake,
                # 500_000_000_00 <= 20_000*(10^decimals)
            )
        ),
        pt.Assert(
            pt.Or(
                stake_duration.get() == FIVE_MINS_STAKING_PERIOD,
                stake_duration.get() == QUARTER_STAKING_PERIOD,
                stake_duration.get() == HALF_YEAR_STAKING_PERIOD,
                stake_duration.get() == ANNUAL_STAKING_PERIOD
            ),
        ),
        (address := pt.abi.Address()).set(pt.Txn.sender()),
        (amount_staked := pt.abi.Uint64()).set(txn.get().asset_amount()),
        (asset_id := pt.abi.Uint64()).set(asset.asset_id()),
        (is_staking := pt.abi.Bool()).set(TRUE),
        (start_timestamp := pt.abi.Uint64()).set(pt.Global.latest_timestamp()),
        (end_timestamp := pt.abi.Uint64()).set(start_timestamp.get() + stake_duration.get()),

        staker.set(
            address,
            amount_staked,
            asset_id,
            is_staking,
            start_timestamp,
            end_timestamp
        ),
        app.state.staker_to_stake[address].set(staker)
    )


# noinspection PyTypeChecker
@app.external
def un_stake(asset: pt.abi.Asset) -> pt.Expr:
    return pt.Seq(
        pt.Assert(app.state.staker_to_stake[pt.Txn.sender()].exists()),
        (staker := Staker()).decode(app.state.staker_to_stake[pt.Txn.sender()].get()),

        (staker_address := pt.abi.Address()).set(staker.address),
        (staker_amount := pt.abi.Uint64()).set(staker.amount),
        (staker_asset := pt.abi.Uint64()).set(staker.asset_id),
        (staker_is_staking := pt.abi.Bool()).set(staker.is_staking),
        (staker_start_timestamp := pt.abi.Uint64()).set(staker.start_timestamp),
        (staker_end_timestamp := pt.abi.Uint64()).set(staker.end_timestamp),

        pt.Assert(staker_is_staking.get() == TRUE),
        pt.Assert(pt.Global.latest_timestamp() >= (staker_end_timestamp.get())),
        pt.Assert(asset.asset_id() == staker_asset.get(), comment="here"),

        (staker_duration := pt.abi.Uint64()).set(staker_end_timestamp.get() - staker_start_timestamp.get()),
        (reward_amount := pt.abi.Uint64()).set(pt.Int(0)),

        calculate_stake_reward(
            stake_amount=staker_amount,
            stake_duration=staker_duration,
            output=reward_amount
        ),
        pt.InnerTxnBuilder.Execute({
            pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
            pt.TxnField.xfer_asset: asset.asset_id(),
            pt.TxnField.asset_receiver: staker_address.get(),
            pt.TxnField.asset_amount: reward_amount.get()
        }),
        staker_is_staking.set(FALSE),
        staker.set(
            staker_address,
            staker_amount,
            staker_asset,
            staker_is_staking,
            staker_start_timestamp,
            staker_end_timestamp
        ),
        pt.Pop(app.state.staker_to_stake[staker_address].delete())
    )


@app.external(read_only=True)
def get_staker(
    staker: pt.abi.Address,
    *,
    output: Staker
) -> pt.Expr:
    return app.state.staker_to_stake[staker].store_into(output)
