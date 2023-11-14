import beaker as bk
import pyteal as pt

from beaker.consts import FALSE, TRUE
from beaker.lib.storage import BoxMapping

BASE_VALUE = pt.Int(10)

FIVE_MINUTES_STAKING_PERIOD = pt.Int(300)
QUARTER_STAKING_PERIOD = pt.Int(7_776_000)
HALF_YEAR_STAKING_PERIOD = pt.Int(15_552_000)
ANNUAL_STAKING_PERIOD = pt.Int(31_536_000)

SECONDS_IN_A_YEAR = pt.Int(31_536_000)


class Staker(pt.abi.NamedTuple):
    """
    Represents a staker with the following instance variables:

    :ivar pt.abi.Address address: The stakers Algorand address.
    :ivar pt.abi.Uint64 amount: The amount staked.
    :ivar pt.abi.Uint64 asset_id: The ID of the asset being staked.
    :ivar pt.abi.Bool is_staking: A boolean indicating if the staker is actively staking.
    :ivar pt.abi.Uint64 start_timestamp: The timestamp when staking started.
    :ivar pt.abi.Uint64 end_timestamp: The timestamp when their staking ends.
    """
    address: pt.abi.Field[pt.abi.Address]
    amount: pt.abi.Field[pt.abi.Uint64]
    asset_id: pt.abi.Field[pt.abi.Uint64]
    is_staking: pt.abi.Field[pt.abi.Bool]
    start_timestamp: pt.abi.Field[pt.abi.Uint64]
    end_timestamp: pt.abi.Field[pt.abi.Uint64]


class State:
    """
    Defines Vest Stake states:

    :ivar bk.GlobalStateValue(bytes) admin_acct: The admin account's address.
    :ivar bk.GlobalStateValue(uint64) asset_id: The unique identifier for the asset.
    :ivar bk.GlobalStateValue(bytes) escrow_address: The address of the escrow account.
    :ivar bk.GlobalStateValue(uint64) min_stake: The minimum staking amount.
    :ivar bk.GlobalStateValue(uint64) max_stake: The maximum staking amount.
    :ivar bk.GlobalStateValue(uint64) annual_rate: The annual staking rate.
    :ivar bk.GlobalStateValue(uint64) vest_decimals: The number of decimal places for $VEST.
    :ivar BoxMapping(abi.Address, Staker) staker_to_stake: A mapping with key of type ``Address``
     and value of type ``Stake``.
    """
    admin_acct = bk.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        default=pt.Bytes("")
    )
    asset_id = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64
    )
    escrow_address = bk.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        default=pt.Bytes("")
    )
    min_stake = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(100) * BASE_VALUE * pt.Int(10_000_000)
    )
    max_stake = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(20_000) * BASE_VALUE * pt.Int(10_000_000)
    )
    annual_rate = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(10)
    )
    vest_decimals = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64
    )
    staker_to_stake = BoxMapping(
        key_type=pt.abi.Address,
        value_type=Staker
    )


app = bk.Application(name="vest_stake", state=State())


# noinspection PyTypeChecker
@pt.Subroutine(pt.TealType.uint64)
def calculate_stake_reward(
    stake_amount: pt.abi.Uint64,
    stake_duration: pt.abi.Uint64
) -> pt.Expr:
    """
    Calculates the stake reward based on the stake amount and duration.

    Arguments must be passed in their order, since this is ``pt.Subroutine`` which only accepts positional args.

    :param pt.abi.Uint64 stake_amount: The amount of the stake.
    :param pt.abi.Uint64 stake_duration: The duration of the stake.

    :rtype: pt.Expr
    """
    return (stake_amount.get() + (
                (stake_amount.get() * app.state.annual_rate * stake_duration.get()) / (pt.Int(100) * SECONDS_IN_A_YEAR))
            )


# noinspection PyTypeChecker
@app.external(authorize=bk.Authorize.only_creator())
def bootstrap(asset: pt.abi.Asset) -> pt.Expr:
    """
    Initializes Vest Stake application's global state, sets admin account, escrow address, asset decimal, and
    opts into the provided asset.

    :param asset: The unique asset ID to be opted into by the escrow address.
    :rtype: pt.Expr.
    """
    return pt.Seq(
        app.initialize_global_state(),
        app.state.admin_acct.set(pt.Global.creator_address()),
        app.state.escrow_address.set(pt.Global.current_application_address()),
        (decimal := pt.AssetParam.decimals(asset.asset_id())),
        pt.Assert(decimal.value() != pt.Int(0), comment="Invalid asset ID."),
        app.state.vest_decimals.set(decimal.value()),
        (escrow_asset_bal := pt.AssetHolding.balance(app.state.escrow_address, asset.asset_id())),
        pt.If(escrow_asset_bal.value() == pt.Int(0), escrow_asset_opt_in(asset=asset)),
    )


def escrow_asset_opt_in(asset: pt.abi.Asset) -> pt.Expr:
    """
    Executes Vest Stake escrow (application) address asset opt in.

    :param pt.abi.Asset asset: The asset to opt be into.
    :rtype: pt.Expr
    """
    return pt.Seq(
        pt.InnerTxnBuilder.Execute({
            pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
            pt.TxnField.xfer_asset: asset.asset_id(),
            pt.TxnField.asset_amount: pt.Int(0),
            pt.TxnField.asset_receiver: pt.Global.current_application_address(),
            pt.TxnField.fee: pt.Int(0)
        })
    )


# noinspection PyTypeChecker
@app.external
def fund_escrow_address(txn: pt.abi.PaymentTransaction) -> pt.Expr:
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
            comment="Invalid transaction amount, receiver or type_enum."
        )
    )


# noinspection PyTypeChecker
@app.external(authorize=bk.Authorize.only_creator())
def set_stake_amounts(
    min_stake: pt.abi.Uint64,
    max_stake: pt.abi.Uint64
) -> pt.Expr:
    """
    Sets the minimum and maximum stake amounts for staking.

    :param pt.abi.Uint64 min_stake: The minimum stake amount.
    :param pt.abi.Uint64 max_stake: The maximum stake amount.
    :rtype: pt.Expr.
    """
    return pt.Seq(
        pt.Assert(
            min_stake.get() > pt.Int(0),
            max_stake.get() > min_stake.get(),
            comment="Min. stake must be greater than 0, and Max. stake must be greater than min. stake."
        ),
        app.state.min_stake.set(min_stake.get() * BASE_VALUE * app.state.vest_decimals),
        app.state.max_stake.set(max_stake.get() * BASE_VALUE * app.state.vest_decimals)
    )


@app.external(authorize=bk.Authorize.only_creator())
def set_annual_rate(annual_rate: pt.abi.Uint64) -> pt.Expr:
    """
    Sets the annual rate.

    :param pt.abi.Uint64 annual_rate: The annual rate.
    :rtype: pt.Expr.
    """
    return app.state.annual_rate.set(annual_rate.get())


@app.external(authorize=bk.Authorize.only_creator())
def set_asset_decimal(asset_decimal: pt.abi.Uint64) -> pt.Expr:
    """
    Sets the asset decimal.

    :param pt.abi.Uint64 asset_decimal: The asset decimal.
    :rtype: pt.Expr.
    """
    return app.state.vest_decimals.set(asset_decimal.get())


@app.external(authorize=bk.Authorize.only_creator())
def set_asset_id(asset_id: pt.abi.Uint64) -> pt.Expr:
    """
    Sets the asset ID.

    :param pt.abi.Uint64 asset_id: The unique asset ID.
    :rtype: pt.Expr.
    """
    return app.state.asset_id.set(asset_id.get())


# noinspection PyTypeChecker
@app.external
def stake(
    asset: pt.abi.Asset,
    stake_duration: pt.abi.Uint64,
    txn: pt.abi.AssetTransferTransaction
) -> pt.Expr:
    """
    Initiates a stake for the specified asset and duration.

    :param pt.abi.Asset asset: The asset to be staked.
    :param pt.abi.Uint64 stake_duration: The duration of the stake.
    :param pt.abi.AssetTransferTransaction txn: The transaction object for the staking operation.
    :rtype: pt.Expr.
    """
    staker = Staker()
    return pt.Seq(
        pt.Assert(
            pt.Not(app.state.staker_to_stake[pt.Txn.sender()].exists()),
            comment="Staker already staking."
        ),
        pt.Assert(
            txn.get().type_enum() == pt.TxnType.AssetTransfer,
            txn.get().asset_receiver() == app.state.escrow_address,
            txn.get().xfer_asset() == asset.asset_id(),
            comment="Invalid transaction type_enum, asset_receiver or xfer_asset."
        ),
        pt.Assert(
            pt.And(
                txn.get().asset_amount() >= app.state.min_stake,
                txn.get().asset_amount() <= app.state.max_stake,
            ),
            comment="Asset amount must be within the min_stake and max_stake."
        ),
        pt.Assert(
            pt.Or(
                stake_duration.get() == FIVE_MINUTES_STAKING_PERIOD,
                stake_duration.get() == QUARTER_STAKING_PERIOD,
                stake_duration.get() == HALF_YEAR_STAKING_PERIOD,
                stake_duration.get() == ANNUAL_STAKING_PERIOD
            ),
            comment="Staking duration must be one of quarter, half year, or annual."
        ),
        (address := pt.abi.Address()).set(pt.Txn.sender()),
        (amount_staked := pt.abi.Uint64()).set(txn.get().asset_amount()),
        (asset_id := pt.abi.Uint64()).set(asset.asset_id()),
        (is_staking := pt.abi.Bool()).set(TRUE),
        (start_timestamp := pt.abi.Uint64()).set(pt.Global.latest_timestamp() + start_timestamp.get()),
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
def unstake(asset: pt.abi.Asset) -> pt.Expr:
    """
    Initiates the unstaking of the specified asset.

    :param asset: The asset to be unstaked.
    :rtype: pt.Expr
    """
    staker = Staker()
    return pt.Seq(
        pt.Assert(
            app.state.staker_to_stake[pt.Txn.sender()].exists(),
            comment="Invalid staker."
        ),

        staker.decode(app.state.staker_to_stake[pt.Txn.sender()].get()),
        (staker_address := pt.abi.Address()).set(staker.address),
        (staker_amount := pt.abi.Uint64()).set(staker.amount),
        (staker_asset := pt.abi.Uint64()).set(staker.asset_id),
        (staker_is_staking := pt.abi.Bool()).set(staker.is_staking),
        (staker_start_timestamp := pt.abi.Uint64()).set(staker.start_timestamp),
        (staker_end_timestamp := pt.abi.Uint64()).set(staker.end_timestamp),
        pt.Assert(
            staker_is_staking.get() == TRUE,
            comment="Staker must be staking."
        ),
        pt.Assert(
            pt.Global.latest_timestamp() >= (staker_end_timestamp.get()),
            comment="Staking period is yet to be over."
        ),
        pt.Assert(
            asset.asset_id() == staker_asset.get(),
            comment="Invalid asset ID."
        ),
        (staker_duration := pt.abi.Uint64()).set(staker_end_timestamp.get() - staker_start_timestamp.get()),
        (reward_amount := pt.abi.Uint64()).set(
            calculate_stake_reward(
                staker_amount,
                staker_duration
            ),
        ),
        pt.InnerTxnBuilder.Execute({
            pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
            pt.TxnField.xfer_asset: asset.asset_id(),
            pt.TxnField.asset_receiver: staker_address.get(),
            pt.TxnField.asset_amount: reward_amount.get(),
            pt.TxnField.fee: pt.Int(0)
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
    """
    Retrieves staker information for the specified staker address and stores it in the output.

    :param staker: The stakers address.
    :param Staker output: The object where staker information will be stored.
    :rtype: pt.Expr.
    """
    return app.state.staker_to_stake[staker].store_into(output)
