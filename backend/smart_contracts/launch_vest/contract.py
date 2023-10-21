import beaker as bk
import pyteal as pt

from beaker.consts import FALSE, TRUE
from beaker.lib.storage import BoxMapping


BASE_VALUE = pt.Int(10)


class Investor(pt.abi.NamedTuple):
    """
    NamedTuple for tracking investment info for investors.

    Attributes:
        pt.abi.Uint64 project_id: ID of Project IDO.
        pt.abi.Uint64 amount_invested: Amount invested by investor.
        pt.abi.Uint64 asset_allocated: Tokens allocated to investor.
        pt.abi.Uint64 claimed: Flag to indicate token claim.
    """
    project_id: pt.abi.Field[pt.abi.Uint64]
    amount_invested: pt.abi.Field[pt.abi.Uint64]
    asset_allocated: pt.abi.Field[pt.abi.Uint64]
    claimed: pt.abi.Field[pt.abi.Bool]


class Project(pt.abi.NamedTuple):
    """
    The following NamedTuple fields are the necessary project details for a particular IDO Project.

    Attributes:
        pt.abi.Address project_owner_address: The project owner address.
        pt.abi.Uint64 start_timestamp: IDO start timestamp.
        pt.abi.Uint64 end_timestamp: IDO end timestamp.
        pt.abi.Uint64 claim_timestamp: IDO claim timestamp.
        pt.abi.Uint64 asset_price: Price of each token in the IDO.
        pt.abi.Uint64 min_investment_per_user: Minimum Algo per user.
        pt.abi.Uint64 max_investment_per_user: Maximum Algo per user.
        pt.abi.Uint64 max_cap: Maximum amount of funds that can be raised during the IDO.
        pt.abi.Uint64 total_tokens_for_sale: Total number of tokens available for purchase in the IDO.
        pt.abi.Bool is_paused: IDO pause flag.
        pt.abi.Bool withdrawn: Withdrawal flag.
        pt.abi.Uint64 total_tokens_sold: Tokens sold during the IDO.
        pt.abi.Uint64 total_amount_raised: Total raised amount.
    """
    project_owner_address: pt.abi.Field[pt.abi.Address]
    start_timestamp: pt.abi.Field[pt.abi.Uint64]
    end_timestamp: pt.abi.Field[pt.abi.Uint64]
    claim_timestamp: pt.abi.Field[pt.abi.Uint64]
    asset_price: pt.abi.Field[pt.abi.Uint64]
    min_investment_per_user: pt.abi.Field[pt.abi.Uint64]
    max_investment_per_user: pt.abi.Field[pt.abi.Uint64]
    max_cap: pt.abi.Field[pt.abi.Uint64]
    total_tokens_for_sale: pt.abi.Field[pt.abi.Uint64]
    is_paused: pt.abi.Field[pt.abi.Bool]
    withdrawn: pt.abi.Field[pt.abi.Bool]
    total_tokens_sold: pt.abi.Field[pt.abi.Uint64]
    total_amount_raised: pt.abi.Field[pt.abi.Uint64]


class ProjectState:
    """
    States of LaunchVest

    Attributes:
        bk.GlobalStateValue project_id: The project id of a particular project.
        bk.GlobalStateValue admin_acct: The Algorand address of LaunchVest owner.
        bk.GlobalStateValue escrow_acct: Escrow address or application address of LaunchVest.
        bk.lib.storage.BoxMapping pid_to_project: A mapping of project id to a particular project.
    """
    admin_acct = bk.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        default=pt.Bytes(""),
    )
    escrow_account = bk.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        default=pt.Bytes(""),
    )
    pid_to_project = BoxMapping(
        key_type=pt.abi.Uint64,
        value_type=Project,
    )
    investor_to_project = BoxMapping(
        key_type=pt.abi.Address,
        value_type=Investor
    )


app = bk.Application(name="launch_vest", state=ProjectState(), descr="LaunchVest Application")


def asset_escrow_opt_in(asset: pt.abi.Asset) -> pt.Expr:
    """
    Executes LaunchVest escrow (application) address asset opt in.

    Args:
        :params pt.abi.Asset asset_id: The ID of the asset to be opted into by the escrow address.

    Returns
        :return: PyTeal expression to execute an asset opt in by the escrow address.
        :rtype: pt.Expr.
    """
    return pt.Seq(
        pt.InnerTxnBuilder.Execute(
            {
                pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
                pt.TxnField.asset_amount: pt.Int(0),
                pt.TxnField.asset_receiver: app.state.escrow_account,
                pt.TxnField.xfer_asset: asset.asset_id(),
            },
        )
    )


def calculate_allocation_for_investor(
    asset_decimal: pt.abi.Uint64,
    amount_bought: pt.abi.Uint64,
    asset_price: pt.abi.Uint64,
    *,
    output: pt.abi.Uint64
) -> pt.Expr:
    """
    Formula for calculating an investor's asset allocation.

    asset_allocated = (amount_bought / asset_price) ^ 10 * decimals.

    Args:
        :param pt.abi.Uint64 asset_decimal: IDO Project asset decimal.
        :param pt.abi.Uint64 amount_bought: The amount of tokens bought in the base token (ALGO).
        :param pt.abi.Uint64 asset_price: The price of the IDO Project asset.
        :param pt.abi.Uint64 output: Result output of the computation.
    Returns:
        :return: Calculated asset allocation for an investor.
        :rtype: pt.Expr
    """
    return output.set((amount_bought.get() / asset_price.get()) * BASE_VALUE ** asset_decimal.get())


@app.external
def bootstrap() -> pt.Expr:
    """
    Initialize LaunchVest global states.

    Returns
        :return: PyTeal Expression to initialize global state.
        :rtype: pt.Expr.
    """
    return pt.Seq(
        app.initialize_global_state(),
        app.state.admin_acct.set(pt.Global.creator_address()),
        app.state.escrow_account.set(pt.Global.current_application_address())
    )


# noinspection PyTypeChecker
@app.external
def list_project(
    asset_id: pt.abi.Asset,

    start_timestamp: pt.abi.Uint64,
    end_timestamp: pt.abi.Uint64,
    claim_timestamp: pt.abi.Uint64,
    asset_price: pt.abi.Uint64,
    min_investment_per_user: pt.abi.Uint64,
    max_investment_per_user: pt.abi.Uint64,
    max_cap: pt.abi.Uint64,
    total_tokens_for_sale: pt.abi.Uint64
) -> pt.Expr:
    """
    Creates a new IDO Project listing on LaunchVest.

    Args:
        :param pt.abi.Asset asset_id: The asset ID of IDO Project.

        :param pt.abi.Uint64 start_timestamp: IDO start timestamp.
        :param pt.abi.Uint64 end_timestamp: IDO end timestamp.
        :param pt.abi.Uint64 claim_timestamp: IDO tokens claim timestamp.
        :param pt.abi.Uint64 asset_price: Price of each token in the IDO.
        :param pt.abi.Uint64 min_investment_per_user: Minimum Algo per user.
        :param pt.abi.Uint64 max_investment_per_user: Maximum Algo per user.
        :param pt.abi.Uint64 max_cap: Maximum amount of funds that can be raised during the IDO.
        :param pt.abi.Uint64 total_tokens_for_sale: Total number of tokens available for purchase in the IDO.

    Returns
        :return: PyTeal expression to list an IDO project on LaunchVest.
        :rtype: pt.Expr.

    Note:
        For our project box: project_id (key) is obtained from asset_id, and this is mapped to an IDO Project (value).
    """
    project = Project()
    project_id = asset_id.asset_id()
    project_id_in_bytes = pt.Itob(project_id)

    project_owner_address = pt.abi.Address()
    is_paused = pt.abi.Bool()
    withdrawn = pt.abi.Bool()

    total_tokens_sold = pt.abi.Uint64()
    total_amount_raised = pt.abi.Uint64()

    return pt.Seq(
        pt.Assert(
            asset_id.asset_id() != pt.Int(0),
            comment="A valid asset id must be provided",
        ),
        pt.Assert(
            asset_price.get() > pt.Int(0),
            comment="Asset price must be greater than 0",
        ),
        pt.Assert(
            min_investment_per_user.get() > pt.Int(0),
            max_investment_per_user.get() > pt.Int(0),
            comment="Min. and max. investment must be greater than 0",
        ),
        pt.Assert(
            min_investment_per_user.get() < max_investment_per_user.get(),
            comment="Min. investment must be lesser than max. investment",
        ),
        pt.Assert(
            start_timestamp.get() > pt.Global.latest_timestamp(),
            end_timestamp.get() > pt.Global.latest_timestamp(),
            claim_timestamp.get() > pt.Global.latest_timestamp(),
            comment="Start, end and claim times must be greater than current time",
        ),
        pt.Assert(
            start_timestamp.get() < end_timestamp.get(),
            comment="Start time must be less than end time",
        ),
        pt.Assert(
            claim_timestamp.get() > start_timestamp.get(),
            claim_timestamp.get() > end_timestamp.get(),
            comment="Claim time must be greater than start and end time",
        ),
        pt.Log(pt.Itob(pt.Global.latest_timestamp())),
        asset_escrow_opt_in(asset=asset_id),
        project_owner_address.set(pt.Txn.sender()),

        is_paused.set(FALSE),
        withdrawn.set(FALSE),

        total_tokens_sold.set(pt.Int(0)),
        total_amount_raised.set(pt.Int(0)),

        project.set(
            project_owner_address,
            start_timestamp,
            end_timestamp,
            claim_timestamp,
            asset_price,
            min_investment_per_user,
            max_investment_per_user,
            max_cap,
            total_tokens_for_sale,
            is_paused,
            withdrawn,
            total_tokens_sold,
            total_amount_raised,
        ),
        app.state.pid_to_project[project_id_in_bytes].set(project)
    )


# noinspection PyTypeChecker
@app.external
def invest(
    asset: pt.abi.Asset,
    txn: pt.abi.PaymentTransaction
) -> pt.Expr:
    """
    Allows interested investors invest in an IDO Project.

    Args:
        :param pt.abi.Asset asset: Asset ID of asset to invest in.
        :param pt.abi.PaymentTransaction txn: PaymentTransaction for given asset.

    Returns:
        :return: PyTeal expression for an investor to invest in an IDO Launchpad.
        :rtype: pt.Expr.
    """
    project_id = asset.asset_id()
    project_id_in_bytes = pt.Itob(project_id)

    investor = Investor()
    abi_investor_project_id = pt.abi.Uint64()
    abi_investor_amount_invested = pt.abi.Uint64()
    abi_investor_asset_allocated = pt.abi.Uint64()
    abi_investor_claimed = pt.abi.Bool()

    return pt.Seq(
        pt.Assert(app.state.pid_to_project[project_id_in_bytes].exists(), comment="1"),

        (project := Project()).decode(app.state.pid_to_project[pt.Itob(project_id)].get()),

        (project_asset_bal_in_escrow := pt.AssetHolding.balance(
            account=app.state.escrow_account,
            asset=asset.asset_id())
         ),
        pt.Assert(project_asset_bal_in_escrow.value() > pt.Int(0), comment="2"),

        (asset_decimal := pt.AssetParam.decimals(asset.asset_id())),
        pt.Assert(asset_decimal.value() != pt.Int(0), comment="3"),

        (project_owner_address := pt.abi.Address()).set(project.project_owner_address),
        (start_timestamp := pt.abi.Uint64()).set(project.start_timestamp),
        (end_timestamp := pt.abi.Uint64()).set(project.end_timestamp),
        (claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),
        (asset_price := pt.abi.Uint64()).set(project.asset_price),
        (min_investment_per_user := pt.abi.Uint64()).set(project.min_investment_per_user),
        (max_investment_per_user := pt.abi.Uint64()).set(project.max_investment_per_user),
        (max_cap := pt.abi.Uint64()).set(project.max_cap),
        (total_tokens_for_sale := pt.abi.Uint64()).set(project.total_tokens_for_sale),
        (is_paused := pt.abi.Bool()).set(project.is_paused),
        (withdrawn := pt.abi.Bool()).set(project.withdrawn),
        (total_tokens_sold := pt.abi.Uint64()).set(project.total_tokens_sold),
        (total_amount_raised := pt.abi.Uint64()).set(project.total_amount_raised),

        pt.Assert(is_paused.get() == FALSE, comment="4"),
        pt.Assert(total_amount_raised.get() < max_cap.get()),

        pt.Assert(
            pt.Global.latest_timestamp() >= start_timestamp.get(),
            pt.Global.latest_timestamp() < end_timestamp.get(),
            comment="5"
        ),
        pt.Assert(
            txn.get().amount() != pt.Int(0),
            txn.get().amount() >= min_investment_per_user.get(),
            txn.get().amount() <= max_investment_per_user.get(),
            txn.get().receiver() == app.state.escrow_account.get(),
            txn.get().type_enum() == pt.TxnType.Payment,
            txn.get().sender() == pt.Txn.sender(),
            comment="6"
        ),

        abi_investor_project_id.set(project_id),
        abi_investor_amount_invested.set(txn.get().amount()),
        abi_investor_claimed.set(FALSE),
        # # Store the result of `calculate_allocation_for_investor` in our `abi_investor_asset_allocated`
        (abi_asset_decimal := pt.abi.Uint64()).set(asset_decimal.value()),
        (abi_amount_bought := pt.abi.Uint64()).set(txn.get().amount()),
        (abi_asset_price := pt.abi.Uint64()).set(asset_price.get()),
        calculate_allocation_for_investor(
            asset_decimal=abi_asset_decimal,
            asset_price=abi_asset_price,
            amount_bought=abi_amount_bought,
            output=abi_investor_asset_allocated
        ),

        investor.set(
            abi_investor_project_id,
            abi_investor_amount_invested,
            abi_investor_asset_allocated,
            abi_investor_claimed
        ),
        app.state.investor_to_project[pt.Txn.sender()].set(investor),

        total_tokens_sold.set(total_tokens_for_sale.get() - abi_investor_asset_allocated.get()),
        total_amount_raised.set(total_amount_raised.get() + abi_investor_amount_invested.get()),

        project.set(
            project_owner_address,
            start_timestamp,
            end_timestamp,
            claim_timestamp,
            asset_price,
            min_investment_per_user,
            max_investment_per_user,
            max_cap,
            total_tokens_for_sale,
            is_paused,
            withdrawn,
            total_tokens_sold,
            total_amount_raised
        )
    )


# TODO: Refactor this function and do a proper test on it.
# noinspection PyTypeChecker
@app.external
def claim_tokens(asset: pt.abi.Asset) -> pt.Expr:
    """
    Allows investors claim their tokens if qualified.

    Args:
        :param pt.abi.Asset asset: Asset ID to be claimed.
    Returns:
        :return: PyTeal expression to let investors claim their tokens.
        :rtype: pt.Expr.
    """
    project_asset_id = asset.asset_id()

    return pt.Seq(
        (project := Project()).decode(app.state.pid_to_project[pt.Itob(project_asset_id)].get()),
        (claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),

        pt.Assert(pt.Global.latest_timestamp() > claim_timestamp.get()),

        (investor := Investor()).decode(app.state.investor_to_project[pt.Txn.sender()].get()),
        pt.Assert(app.state.pid_to_project[pt.Itob(project_asset_id)].exists()),

        (project_id := pt.abi.Uint64()).set(investor.project_id),
        (amount_invested := pt.abi.Uint64()).set(investor.amount_invested),
        (asset_allocated := pt.abi.Uint64()).set(investor.asset_allocated),
        (claimed := pt.abi.Bool()).set(investor.claimed),

        pt.Assert(project_id.get() == project_asset_id),
        pt.Assert(amount_invested.get() > pt.Int(0)),
        pt.Assert(asset_allocated.get() > pt.Int(0)),
        pt.Assert(claimed.get() == FALSE),

        pt.InnerTxnBuilder.Execute({
            pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
            pt.TxnField.asset_amount: asset_allocated.get(),
            pt.TxnField.asset_receiver: pt.Txn.sender(),
            pt.TxnField.xfer_asset: asset.asset_id(),
        }),

        (claimed := pt.abi.Bool()).set(TRUE),
        investor.set(
            project_id,
            amount_invested,
            asset_allocated,
            claimed
        )
    )


@app.external
def pause() -> pt.Expr:
    return pt.Seq()


@app.external
def unpause() -> pt.Expr:
    return pt.Seq()


@app.external
def deposit_ido_tokens() -> pt.Expr:
    """Alternate function for token deposit."""
    return pt.Seq()


@app.external
def change_end_time() -> pt.Expr:
    return pt.Seq()


@app.external
def withdraw_amount_raised() -> pt.Expr:
    """Charge fee before withdrawal"""
    return pt.Seq()


@app.external
def change_launchpad_admin() -> pt.Expr:
    return pt.Seq()


"""Implement IDO Insurance."""

@app.external
def get_project(
    project_id: pt.abi.Uint64,
    *,
    output: Project
) -> pt.Expr:
    """
    Retrieves a specific IDO project.

    Args:
        :param pt.abi.Uint64 project_id: The unique project ID obtained from an asset_id.
        :param Project output: An object to store the retrieved IDO project.
    Returns:
        :return: A valid IDO project.
        :rtype: pt.Expr.
    """
    return app.state.pid_to_project[project_id].store_into(output)
