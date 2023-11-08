import beaker as bk
import pyteal as pt

from beaker.consts import FALSE, TRUE
from beaker.lib.storage import BoxMapping

from backend.smart_contracts.launch_vest.formula_helpers import (
    calculate_allocation_for_investor,
    calculate_disbursement,
    calculate_proceeds_after_fee_deduction,
    calculate_project_max_cap
)


USDC_ASSET_ID = pt.Int(10458941)
LAUNCH_VEST_FEE = pt.Int(10)  # 10%
PERCENTAGE = pt.Int(10)

RECLAIM_WINDOW = pt.Int(1_209_600)

ONE_MINUTE = pt.Int(60)
QUARTERLY_VESTING_PERIOD = pt.Int(7_776_000)
HALF_YEAR_VESTING_PERIOD = pt.Int(15_552_000)
YEARLY_VESTING_PERIOD = pt.Int(31_536_000)


class Investor(pt.abi.NamedTuple):
    """
    Represents an investor, extends ``pt.abi.NamedTuple``.

    :ivar pt.abi.Address address: The Algorand address of the investor.
    :ivar pt.abi.Uint64 project_id: The unique identifier of the project.
    :ivar pt.abi.Uint64 investment_amount: The amount of the investment in Algos.
    :ivar pt.abi.Uint64 asset_allocation: The amount of allocated assets.
    :ivar pt.abi.Uint64 asset_claim_timestamp: The timestamp an investor claims their asset.
    :ivar pt.abi.Bool claimed_ido_asset: A boolean indicating whether the investor has claimed assets.
    :ivar pt.abi.Bool reclaimed_investment: A boolean indicating whether the investor has reclaimed their investment.
    """
    address: pt.abi.Field[pt.abi.Address]
    project_id: pt.abi.Field[pt.abi.Uint64]
    investment_amount: pt.abi.Field[pt.abi.Uint64]
    asset_allocation: pt.abi.Field[pt.abi.Uint64]
    asset_claim_timestamp: pt.abi.Field[pt.abi.Uint64]
    claimed_ido_asset: pt.abi.Field[pt.abi.Bool]
    reclaimed_investment: pt.abi.Field[pt.abi.Bool]


class Project(pt.abi.NamedTuple):
    """
    Represents a project, extends ``pt.abi.NamedTuple``.

    :ivar pt.abi.Address owner_address: The Algorand address of the project owner.
    :ivar pt.abi.Uint64 start_timestamp: The timestamp when the project starts.
    :ivar pt.abi.Uint64 end_timestamp: The timestamp when the project ends.
    :ivar pt.abi.Uint64 claim_timestamp: The timestamp for asset claiming.
    :ivar pt.abi.Uint64 asset_id: The unique asset ID of the Project.
    :ivar pt.abi.String image_url: The project image url.
    :ivar pt.abi.Uint64 price_per_asset: The price of each asset.
    :ivar pt.abi.Uint64 min_investment_per_investor: The minimum investment per user.
    :ivar pt.abi.Uint64 max_investment_per_investor: The maximum investment per user.
    :ivar pt.abi.Uint64 max_cap: The maximum investment cap.
    :ivar pt.abi.Uint64 total_assets_for_sale: The total assets available for sale.
    :ivar pt.abi.Bool is_paused: A boolean indicating whether the project is paused.
    :ivar pt.abi.Bool initiated_withdrawal: A boolean indicating whether project owner have initiated withdrawal.
    :ivar pt.abi.Uint64 total_assets_sold: The total assets sold.
    :ivar pt.abi.Uint64 total_amount_raised: The total amount raised.
    :ivar pt.abi.Uint64 amount_withdrawn: The total amount withdrawn so far.
    :ivar pt.abi.Uint64 vesting_schedule: The lockup period of amount raised for this project.
    """
    owner_address: pt.abi.Field[pt.abi.Address]
    start_timestamp: pt.abi.Field[pt.abi.Uint64]
    end_timestamp: pt.abi.Field[pt.abi.Uint64]
    claim_timestamp: pt.abi.Field[pt.abi.Uint64]
    asset_id: pt.abi.Field[pt.abi.Uint64]
    image_url: pt.abi.Field[pt.abi.String]
    price_per_asset: pt.abi.Field[pt.abi.Uint64]
    min_investment_per_investor: pt.abi.Field[pt.abi.Uint64]
    max_investment_per_investor: pt.abi.Field[pt.abi.Uint64]
    max_cap: pt.abi.Field[pt.abi.Uint64]
    total_assets_for_sale: pt.abi.Field[pt.abi.Uint64]
    is_paused: pt.abi.Field[pt.abi.Bool]
    initiated_withdrawal: pt.abi.Field[pt.abi.Bool]
    total_assets_sold: pt.abi.Field[pt.abi.Uint64]
    total_amount_raised: pt.abi.Field[pt.abi.Uint64]
    amount_withdrawn: pt.abi.Field[pt.abi.Uint64]
    vesting_schedule: pt.abi.Field[pt.abi.Uint64]


class ProjectState:
    """
    Defines Launch Vest states.

    :ivar bk.GlobalStateValue(bytes) admin_acct: A global state value representing the administrator's account.
    :ivar bk.GlobalStateValue(bytes) escrow_address: A global state value representing the escrow address.
    :ivar BoxMapping(abi.Uint64, Project) pid_to_project: A box mapping with key of type ``Uint64`` and value of type
    ``Project``.
    :ivar BoxMapping(abi.Address, Investor) investor_to_project: A box mapping with key of type ``Address`` and
    value of type ``Investor``.
    """
    admin_acct = bk.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        default=pt.Bytes(""),
    )
    escrow_address = bk.GlobalStateValue(
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


def escrow_asset_opt_in(asset: pt.abi.Asset) -> pt.Expr:
    """
    Executes LaunchVest escrow (application) address asset opt in.

    :param pt.abi.Asset asset: The asset to be opted into.
    :rtype: pt.Expr
    """
    return pt.Seq(
        pt.InnerTxnBuilder.Execute(
            {
                pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
                pt.TxnField.asset_amount: pt.Int(0),
                pt.TxnField.asset_receiver: app.state.escrow_address,
                pt.TxnField.xfer_asset: asset.asset_id(),
                pt.TxnField.fee: pt.Int(0)
            },
        )
    )


# noinspection PyTypeChecker
@app.external(authorize=bk.Authorize.only_creator())
def bootstrap(asset: pt.abi.Asset) -> pt.Expr:
    """
    Initializes Launch Vest application's global state, sets the admin account, and sets the escrow address.

    :rtype: pt.Expr.
    """
    return pt.Seq(
        app.initialize_global_state(),
        app.state.admin_acct.set(pt.Global.creator_address()),
        app.state.escrow_address.set(pt.Global.current_application_address()),
        (escrow_asset_bal := pt.AssetHolding.balance(app.state.escrow_address, asset.asset_id())),
        pt.If(escrow_asset_bal.value() == pt.Int(0), escrow_asset_opt_in(asset=asset)),
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
            comment="Invalid amount, receiver or type_enum."
        )
    )


# noinspection PyTypeChecker
@app.external
def list_project(
    asset_id: pt.abi.Asset,
    image_url: pt.abi.String,
    start_timestamp: pt.abi.Uint64,
    end_timestamp: pt.abi.Uint64,
    claim_timestamp: pt.abi.Uint64,
    price_per_asset: pt.abi.Uint64,
    min_investment_per_investor: pt.abi.Uint64,
    max_investment_per_investor: pt.abi.Uint64,
    vesting_schedule: pt.abi.Uint64
) -> pt.Expr:
    """
    Lists a new IDO Project on LaunchVest.

    :param pt.abi.Asset asset_id: The unique identifier of the asset.
    :param image_url: The project image url.
    :param pt.abi.Uint64 start_timestamp: The timestamp when the project starts.
    :param pt.abi.Uint64 end_timestamp: The timestamp when the project ends.
    :param pt.abi.Uint64 claim_timestamp: The timestamp for asset claiming.
    :param pt.abi.Uint64 price_per_asset: The price of each asset.
    :param pt.abi.Uint64 min_investment_per_investor: The minimum investment per user.
    :param pt.abi.Uint64 max_investment_per_investor: The maximum investment per user.
    :param pt.abi.Uint64 vesting_schedule: The vesting schedule of project.
    :rtype: pt.Expr.

    .. Note::
        project_id (key) is obtained from asset_id of the provided asset, and this is mapped to a Project (value).
    """
    project = Project()
    project_id = asset_id.asset_id()
    project_id_bytes = pt.Itob(project_id)

    return pt.Seq(
        (asset_total := pt.AssetParam.total(asset_id.asset_id())),
        # TODO: Uncomment this, fix price and decimal issues!
        # pt.Assert(
        #     pt.Not(app.state.pid_to_project[project_id_bytes].exists()),
        #     comment="Project already exists!"
        # ),
        # Checks if its a valid asset ID provided.
        pt.Assert(
            asset_total.value() > pt.Int(0),
            comment="A valid asset ID must be provided",
        ),
        pt.Assert(
            price_per_asset.get() > pt.Int(0),
            comment="Asset price must be greater than 0",
        ),
        pt.Assert(
            min_investment_per_investor.get() > pt.Int(0),
            max_investment_per_investor.get() > min_investment_per_investor.get(),
            comment="Min. must be greater than 0, and max investment must be greater than min. investment.",
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
        pt.Assert(
            pt.Or(
                vesting_schedule.get() == ONE_MINUTE,
                vesting_schedule.get() == QUARTERLY_VESTING_PERIOD,
                vesting_schedule.get() == HALF_YEAR_VESTING_PERIOD,
                vesting_schedule.get() == YEARLY_VESTING_PERIOD,
            ),
            comment="Vesting schedule must fall between quarterly, half_year or yearly periods."
        ),

        escrow_asset_opt_in(asset=asset_id),
        (project_owner_address := pt.abi.Address()).set(pt.Txn.sender()),
        (project_asset_id := pt.abi.Uint64()).set(asset_id.asset_id()),
        (project_max_cap := pt.abi.Uint64()).set(pt.Int(0)),
        (project_total_assets_for_sale := pt.abi.Uint64()).set(pt.Int(0)),
        (project_is_paused := pt.abi.Bool()).set(FALSE),
        (project_initiated_withdrawal := pt.abi.Bool()).set(FALSE),
        (project_total_assets_sold := pt.abi.Uint64()).set(pt.Int(0)),
        (project_total_amount_raised := pt.abi.Uint64()).set(pt.Int(0)),
        (project_amount_withdrawn := pt.abi.Uint64()).set(pt.Int(0)),
        (project_vesting_schedule := pt.abi.Uint64()).set(pt.Global.latest_timestamp() + vesting_schedule.get()),

        project.set(
            project_owner_address,
            start_timestamp,
            end_timestamp,
            claim_timestamp,
            project_asset_id,
            image_url,
            price_per_asset,
            min_investment_per_investor,
            max_investment_per_investor,
            project_max_cap,
            project_total_assets_for_sale,
            project_is_paused,
            project_initiated_withdrawal,
            project_total_assets_sold,
            project_total_amount_raised,
            project_amount_withdrawn,
            project_vesting_schedule
        ),
        app.state.pid_to_project[project_id_bytes].set(project),
    )


# noinspection PyTypeChecker
@app.external
def deposit_ido_assets(
    txn: pt.abi.AssetTransferTransaction,
    asset: pt.abi.Asset
) -> pt.Expr:
    """
    Allows depositing IDO assets using the provided transaction and asset.

    :param pt.abi.AssetTransferTransaction txn: The asset transfer transaction for the deposit.
    :param pt.abi.Asset asset: The asset to be deposited.
    :rtype: pt.Expr.
    """
    project = Project()
    project_id = asset.asset_id()
    project_id_bytes = pt.Itob(project_id)

    return pt.Seq(
        pt.Assert(
            app.state.pid_to_project[project_id_bytes].exists(),
            comment="A valid project ID must be provided"
        ),

        project.decode(app.state.pid_to_project[project_id_bytes].get()),
        (project_owner_address := pt.abi.Address()).set(project.owner_address),
        pt.Assert(
            pt.Txn.sender() == project_owner_address.get(),
            comment="Transaction sender must be the project owner."
        ),
        pt.Assert(
            txn.get().asset_amount() > pt.Int(0),
            txn.get().asset_receiver() == app.state.escrow_address,
            txn.get().type_enum() == pt.TxnType.AssetTransfer,
            txn.get().xfer_asset() == asset.asset_id(),
            txn.get().sender() == project_owner_address.get(),
            comment="Invalid asset_amount, asset_receiver, type_enum, xfer_asset or sender."
        ),

        (project_start_timestamp := pt.abi.Uint64()).set(project.start_timestamp),
        (project_end_timestamp := pt.abi.Uint64()).set(project.end_timestamp),
        (project_claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),
        (project_asset_id := pt.abi.Uint64()).set(project.asset_id),
        (project_image_url := pt.abi.String()).set(project.image_url),
        (project_price_per_asset := pt.abi.Uint64()).set(project.price_per_asset),
        (project_min_investment_per_investor := pt.abi.Uint64()).set(project.min_investment_per_investor),
        (project_max_investment_per_investor := pt.abi.Uint64()).set(project.max_investment_per_investor),
        (project_total_assets_for_sale := pt.abi.Uint64()).set(txn.get().asset_amount()),
        (project_is_paused := pt.abi.Bool()).set(project.is_paused),
        (project_initiated_withdrawal := pt.abi.Bool()).set(project.initiated_withdrawal),
        (project_total_assets_sold := pt.abi.Uint64()).set(project.total_assets_sold),
        (project_total_amount_raised := pt.abi.Uint64()).set(project.total_amount_raised),
        (project_amount_withdrawn := pt.abi.Uint64()).set(project.amount_withdrawn),
        (project_vesting_schedule := pt.abi.Uint64()).set(project.vesting_schedule),
        (project_max_cap := pt.abi.Uint64()).set(
            calculate_project_max_cap(
                project_total_assets_for_sale,
                project_price_per_asset
            )
        ),

        project.set(
            project_owner_address,
            project_start_timestamp,
            project_end_timestamp,
            project_claim_timestamp,
            project_asset_id,
            project_image_url,
            project_price_per_asset,
            project_min_investment_per_investor,
            project_max_investment_per_investor,
            project_max_cap,
            project_total_assets_for_sale,
            project_is_paused,
            project_initiated_withdrawal,
            project_total_assets_sold,
            project_total_amount_raised,
            project_amount_withdrawn,
            project_vesting_schedule
        ),
        app.state.pid_to_project[project_id_bytes].set(project)
    )


# noinspection PyTypeChecker
@pt.Subroutine(pt.TealType.uint64)
def investor_algo_payment(
    min_investment: pt.abi.Uint64,
    max_investment: pt.abi.Uint64,
    txn: pt.abi.Transaction,
) -> pt.Expr:
    """
    ALGO transaction from investor, investment must be within the min and max limits.

    Arguments must be passed in their order, since this is ``pt.Subroutine`` which only accepts positional args.

    :param pt.abi.Uint64 min_investment: The minimum investment amount allowed.
    :param pt.abi.Uint64 max_investment: The maximum investment amount allowed.
    :param pt.abi.Transaction txn: The transaction containing investment details (type_enum must be of Payment).
    :rtype: pt.Expr.
    """
    return pt.Seq(
        pt.Assert(
            txn.get().type_enum() == pt.TxnType.Payment,
            comment="Transaction type must be Payment."
        ),
        pt.Assert(
            txn.get().receiver() == app.state.escrow_address.get(),
            comment="Invalid receiver or transaction type."
        ),
        pt.Assert(
            pt.Or(
                txn.get().amount() >= min_investment.get(),
                txn.get().amount() <= max_investment.get(),
            ),
            comment="Asset amount must be greater or equal to min_investment"
                    " and must be less than or equal to max_investment."
        ),
        pt.Return(txn.get().amount())
    )


# noinspection PyTypeChecker
@pt.Subroutine(pt.TealType.uint64)
def investor_usdc_payment(
    min_investment: pt.abi.Uint64,
    max_investment: pt.abi.Uint64,
    asset_id: pt.abi.Asset,
    txn: pt.abi.Transaction
) -> pt.Expr:
    """
    USDC transaction from investor, investment must be within the min and max limits.

    Arguments must be passed in their order, since this is ``pt.Subroutine`` which only accepts positional args.

    :param pt.abi.Uint64 min_investment: The minimum investment amount allowed.
    :param pt.abi.Uint64 max_investment: The maximum investment amount allowed.
    :param pt.abi.Uint64 asset_id: The unique ID of the asset.
    :param pt.abi.Transaction txn: The transaction containing investment details (type_enum must be of AssetTransfer).
    :rtype: pt.Expr
    """
    return pt.Seq(
        pt.Assert(
            txn.get().type_enum() == pt.TxnType.AssetTransfer,
            comment="Transaction type must be AssetTransfer."
        ),
        pt.Assert(
            asset_id.asset_id() == USDC_ASSET_ID,
            comment="Invalid asset ID for USDC."
        ),
        pt.Assert(
            txn.get().asset_receiver() == app.state.escrow_address.get(),
            txn.get().xfer_asset() == asset_id.asset_id(),
            comment="Invalid receiver or transaction type."
        ),
        pt.Assert(
            pt.Or(
                txn.get().asset_amount() >= min_investment.get(),
                txn.get().asset_amount() <= max_investment.get(),
            ),
            comment="Asset amount must be greater or equal to min_investment"
                    " and must be less than or equal to max_investment."
        ),
        pt.Return(txn.get().asset_amount())
    )


# noinspection PyTypeChecker
@app.external
def invest(
    is_staking: pt.abi.Bool,
    project_id: pt.abi.Asset,
    txn: pt.abi.Transaction,
    investment_asset_id: pt.abi.Asset
) -> pt.Expr:
    """
    Executes an investment transaction for a project.

    :param pt.abi.Bool is_staking: Indicates whether the investor is staking $VEST
    :param pt.abi.Asset project_id: The project (asset) ID to invest in.
    :param pt.abi.PaymentTransaction txn: The payment transaction for the investment.
    :param pt.abi.Asset investment_asset_id: The unique ID to of the asset.
    :rtype: pt.Expr.
    """
    investor = Investor()

    project = Project()
    project_asset_id = project_id.asset_id()
    project_id = project_id.asset_id()
    project_id_bytes = pt.Itob(project_id)

    return pt.Seq(
        pt.Assert(
            is_staking.get() == TRUE,
            comment="Investor must be staking $VEST."
        ),
        pt.Assert(
            app.state.pid_to_project[project_id_bytes].exists(),
            comment="A valid project ID must be provided"
        ),

        project.decode(app.state.pid_to_project[project_id_bytes].get()),
        (project_asset_bal_in_escrow := pt.AssetHolding.balance(
            account=app.state.escrow_address,
            asset=project_asset_id
        )
         ),
        pt.Assert(
            project_asset_bal_in_escrow.value() > pt.Int(0),
            comment="Project assets must be available in escrow."
        ),

        (project_owner_address := pt.abi.Address()).set(project.owner_address),
        (project_start_timestamp := pt.abi.Uint64()).set(project.start_timestamp),
        (project_end_timestamp := pt.abi.Uint64()).set(project.end_timestamp),
        (project_claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),
        (project_asset_id := pt.abi.Uint64()).set(project.asset_id),
        (project_image_url := pt.abi.String()).set(project.image_url),
        (project_price_per_asset := pt.abi.Uint64()).set(project.price_per_asset),
        (project_min_investment_per_user := pt.abi.Uint64()).set(project.min_investment_per_investor),
        (project_max_investment_per_user := pt.abi.Uint64()).set(project.max_investment_per_investor),
        (project_max_cap := pt.abi.Uint64()).set(project.max_cap),
        (project_total_assets_for_sale := pt.abi.Uint64()).set(project.total_assets_for_sale),
        (project_is_paused := pt.abi.Bool()).set(project.is_paused),
        (project_initiated_withdrawal := pt.abi.Bool()).set(project.initiated_withdrawal),
        (project_total_assets_sold := pt.abi.Uint64()).set(project.total_assets_sold),
        (project_total_amount_raised := pt.abi.Uint64()).set(project.total_amount_raised),
        (project_amount_withdrawn := pt.abi.Uint64()).set(project.amount_withdrawn),
        (project_vesting_schedule := pt.abi.Uint64()).set(project.vesting_schedule),

        pt.Assert(
            project_is_paused.get() == FALSE,
            comment="Project must not be paused."
        ),
        pt.Assert(
            project_total_amount_raised.get() < project_max_cap.get(),
            comment="Total amount raised must be less than max. cap"
        ),
        pt.Assert(
            pt.Global.latest_timestamp() >= project_start_timestamp.get(),
            pt.Global.latest_timestamp() < project_end_timestamp.get(),
            comment="Project must be live and ongoing."
        ),
        pt.Assert(
            pt.Or(
                txn.get().type_enum() == pt.TxnType.Payment,
                txn.get().type_enum() == pt.TxnType.AssetTransfer
            ),
            comment="Invalid transaction type. Must be of type Payment or AssetTransfer."
        ),

        (investor_investment_amount := pt.abi.Uint64()).set(pt.Int(0)),
        pt.If(txn.get().xfer_asset() == pt.Int(0))
        .Then(
            investor_investment_amount.set(
                investor_algo_payment(
                    project_min_investment_per_user,
                    project_max_investment_per_user,
                    txn
                )
            ),
        ).Else(
            investor_investment_amount.set(
                investor_usdc_payment(
                    project_min_investment_per_user,
                    project_max_investment_per_user,
                    investment_asset_id,
                    txn
                )
            )
        ),
        (investor_address := pt.abi.Address()).set(pt.Txn.sender()),
        (investor_project_id := pt.abi.Uint64()).set(project_id),
        (investor_asset_claim_timestamp := pt.abi.Uint64()).set(pt.Int(0)),
        (investor_claimed_ido_asset := pt.abi.Bool()).set(FALSE),
        (investor_reclaimed_investment := pt.abi.Bool()).set(FALSE),
        #  Modify this, allocation should be set off-chain.
        (investor_asset_allocation := pt.abi.Uint64()).set(
            calculate_allocation_for_investor(
                investor_investment_amount,
                project_price_per_asset,
            )
        ),
        (investor_asset_allocation.set(investor_asset_allocation.get())),
        investor.set(
            investor_address,
            investor_project_id,
            investor_investment_amount,
            investor_asset_allocation,
            investor_asset_claim_timestamp,
            investor_claimed_ido_asset,
            investor_reclaimed_investment
        ),
        app.state.investor_to_project[investor_address].set(investor),

        project_total_assets_sold.set(project_total_assets_for_sale.get() - investor_asset_allocation.get()),
        project_total_amount_raised.set(project_total_amount_raised.get() + investor_investment_amount.get()),

        project.set(
            project_owner_address,
            project_start_timestamp,
            project_end_timestamp,
            project_claim_timestamp,
            project_asset_id,
            project_image_url,
            project_price_per_asset,
            project_min_investment_per_user,
            project_max_investment_per_user,
            project_max_cap,
            project_total_assets_for_sale,
            project_is_paused,
            project_initiated_withdrawal,
            project_total_assets_sold,
            project_total_amount_raised,
            project_amount_withdrawn,
            project_vesting_schedule
        ),
        app.state.pid_to_project[project_id_bytes].set(project)
    )


# noinspection PyTypeChecker
@app.external
def claim_ido_asset(
    project_id: pt.abi.Asset,
    is_staking: pt.abi.Bool
) -> pt.Expr:
    """
    Allows users to claim a specific IDO Project asset.

    :param pt.abi.Asset project_id: Project (asset) ID to be claimed.
    :param is_staking: Flag to indicate whether investor is staking $VEST.
    :rtype: pt.Expr.
    """
    investor = Investor()

    project = Project()
    project_asset_id = project_id.asset_id()
    project_id_bytes = pt.Itob(project_asset_id)

    return pt.Seq(
        pt.Assert(
            app.state.investor_to_project[pt.Txn.sender()].exists(),
            comment="Invalid investor."
        ),
        pt.Assert(
            app.state.pid_to_project[project_id_bytes].exists(),
            comment="Invalid project."
        ),

        project.decode(app.state.pid_to_project[pt.Itob(project_asset_id)].get()),
        (project_claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),
        pt.Assert(
            pt.Global.latest_timestamp() >= project_claim_timestamp.get(),
            comment="Asset claiming hasn't begun."
        ),

        investor.decode(app.state.investor_to_project[pt.Txn.sender()].get()),
        (investor_address := pt.abi.Address()).set(investor.address),
        (investor_project_id := pt.abi.Uint64()).set(investor.project_id),
        (investor_investment_amount := pt.abi.Uint64()).set(investor.investment_amount),
        (investor_asset_allocation := pt.abi.Uint64()).set(investor.asset_allocation),
        (investor_asset_claim_timestamp := pt.abi.Uint64()).set(investor.asset_claim_timestamp),
        (investor_claimed_ido_asset := pt.abi.Bool()).set(investor.claimed_ido_asset),
        (investor_reclaimed_investment := pt.abi.Bool()).set(investor.reclaimed_investment),
        pt.Assert(
            is_staking.get() == TRUE,
            comment="Investor must be staking."
        ),
        pt.Assert(
            investor_investment_amount.get() > pt.Int(0),
            comment="Investor amount must be greater than 0."
        ),
        pt.Assert(
            investor_asset_allocation.get() > pt.Int(0),
            comment="Investor asset allocation must be greater than 0."
        ),
        pt.Assert(
            investor_asset_claim_timestamp.get() == pt.Int(0),
            comment="Investor claim_timestamp must be 0."
        ),
        pt.Assert(
            investor_claimed_ido_asset.get() == FALSE,
            comment="Investor must have not claimed their allocation."
        ),
        pt.Assert(
            investor_reclaimed_investment.get() == FALSE,
            comment="Investor must have not reclaimed their investment."
        ),
        pt.InnerTxnBuilder.Execute({
            pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
            pt.TxnField.asset_amount: investor_asset_allocation.get(),
            pt.TxnField.asset_receiver: investor_address.get(),
            pt.TxnField.xfer_asset: project_asset_id,
            pt.TxnField.fee: pt.Int(0)
        }),

        investor_asset_claim_timestamp.set(pt.Global.latest_timestamp()),
        investor_claimed_ido_asset.set(TRUE),
        investor.set(
            investor_address,
            investor_project_id,
            investor_investment_amount,
            investor_asset_allocation,
            investor_asset_claim_timestamp,
            investor_claimed_ido_asset,
            investor_reclaimed_investment
        ),
        app.state.investor_to_project[investor_address.get()].set(investor)
    )


# noinspection PyTypeChecker
@app.external
def reclaim_investment(
    project_id: pt.abi.Asset,
    is_staking: pt.abi.Bool,
    investment_asset_id: pt.abi.Asset
) -> pt.Expr:
    """
    Allows investors to reclaim their investment.

    :param pt.abi.Asset project_id: Project (asset) ID to be claimed.
    :param is_staking: Flag to indicate whether investor is current staking $VEST.
    :param investment_asset_id: The unique asset ID of investment (ALGO, USDC).
    :rtype: pt.Expr.
    """
    investor = Investor()
    project = Project()

    project_asset_id = project_id.asset_id()
    project_id_bytes = pt.Itob(project_asset_id)

    return pt.Seq(
        pt.Assert(
            app.state.investor_to_project[pt.Txn.sender()].exists(),
            comment="Invalid investor."
        ),
        pt.Assert(
            app.state.pid_to_project[project_id_bytes].exists(),
            comment="Invalid project ID."
        ),

        investor.decode(app.state.investor_to_project[pt.Txn.sender()].get()),
        (investor_address := pt.abi.Address()).set(investor.address),
        (investor_project_id := pt.abi.Uint64()).set(investor.project_id),
        (investor_investment_amount := pt.abi.Uint64()).set(investor.investment_amount),
        (investor_asset_allocation := pt.abi.Uint64()).set(investor.asset_allocation),
        (investor_claimed_ido_asset := pt.abi.Bool()).set(investor.claimed_ido_asset),
        (investor_asset_claim_timestamp := pt.abi.Uint64()).set(investor.asset_claim_timestamp),
        (investor_reclaimed_investment := pt.abi.Bool()).set(investor.reclaimed_investment),

        project.decode(app.state.investor_to_project[project_id_bytes].get()),
        (project_claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),

        (asset_bal := pt.AssetHolding.balance(app.state.escrow_address.get(), project_asset_id)),
        pt.Assert(
            asset_bal.value() > pt.Int(0),
            comment="Project assets must be available in escrow."
        ),
        pt.Assert(
            is_staking.get() == TRUE,
            comment="Investor must be staking $VEST."
        ),
        pt.Assert(
            investor_asset_allocation.get() > pt.Int(0),
            comment="Investor asset allocation must be greater than 0."
        ),
        pt.Assert(
            investor_claimed_ido_asset.get() == FALSE,
            comment="Investor must have not claimed their asset allocation."
        ),
        pt.Assert(
            investor_reclaimed_investment.get() == FALSE,
            comment="Investor must have not reclaimed investment."
        ),
        pt.Assert(
            RECLAIM_WINDOW >= (pt.Global.latest_timestamp() - project_claim_timestamp.get()),
            comment="Claim must be within reclaim window."
        ),
        pt.If(investment_asset_id.asset_id() == pt.Int(0))
        .Then(
            pt.InnerTxnBuilder.Execute({
                pt.TxnField.type_enum: pt.TxnType.Payment,
                pt.TxnField.receiver: investor_address.get(),
                pt.TxnField.amount: investor_investment_amount.get(),
                pt.TxnField.fee: pt.Int(0)
            }),
        ).Else(
            pt.Assert(
                investment_asset_id.asset_id() == USDC_ASSET_ID,
                comment=f"Reclaim asset must be USDC asset ID: {USDC_ASSET_ID}"
            ),
            pt.InnerTxnBuilder.Execute({
                pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
                pt.TxnField.asset_receiver: investor_address.get(),
                pt.TxnField.asset_amount: investor_investment_amount.get(),
                pt.TxnField.xfer_asset: investment_asset_id.asset_id(),
                pt.TxnField.fee: pt.Int(0)
            }),
        ),
        investor_investment_amount.set(pt.Int(0)),
        investor_asset_allocation.set(pt.Int(0)),
        investor_reclaimed_investment.set(TRUE),
        investor.set(
            investor_address,
            investor_project_id,
            investor_investment_amount,
            investor_asset_allocation,
            investor_asset_claim_timestamp,
            investor_claimed_ido_asset,
            investor_reclaimed_investment
        ),
        app.state.investor_to_project[investor_address.get()].set(investor)
    )


# noinspection PyTypeChecker
def disburse(
    amount: pt.abi.Uint64,
    receiver: pt.abi.Address,
) -> pt.Expr:
    """
    Disburses amount to receiver from escrow.

    :param amount: Amount to be disbursed.
    :param receiver: Receiver of amount to be disbursed.
    :rtype: pt.Expr.
    """
    return pt.Seq(
        pt.InnerTxnBuilder.Execute({
            pt.TxnField.type_enum: pt.TxnType.Payment,
            pt.TxnField.amount: amount.get(),
            pt.TxnField.receiver: receiver.get(),
            pt.TxnField.fee: pt.Int(0)
        }),
    )


# noinspection PyTypeChecker
@app.external
def withdraw_amount_raised(project_id: pt.abi.Uint64) -> pt.Expr:
    """
    Allows the withdrawal of the amount raised for a specific project, retains LaunchVest fee in the escrow.

    :param pt.abi.Uint64 project_id: The unique identifier of the project for which funds are withdrawn.
    :rtype: pt.Expr
    """
    project = Project()
    project_id_bytes = pt.Itob(project_id.get())

    return pt.Seq(
        pt.Assert(
            app.state.pid_to_project[project_id_bytes].exists(),
            comment="Invalid project ID."
        ),

        project.decode(app.state.pid_to_project[project_id_bytes].get()),
        (project_owner_address := pt.abi.Address()).set(project.owner_address),
        (project_start_timestamp := pt.abi.Uint64()).set(project.start_timestamp),
        (project_end_timestamp := pt.abi.Uint64()).set(project.end_timestamp),
        (project_claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),
        (project_asset_id := pt.abi.Uint64()).set(project.asset_id),
        (project_image_url := pt.abi.String()).set(project.image_url),
        (project_price_per_asset := pt.abi.Uint64()).set(project.price_per_asset),
        (project_min_investment_per_investor := pt.abi.Uint64()).set(project.min_investment_per_investor),
        (project_max_investment_per_investor := pt.abi.Uint64()).set(project.max_investment_per_investor),
        (project_max_cap := pt.abi.Uint64()).set(project.max_cap),
        (project_total_assets_for_sale := pt.abi.Uint64()).set(project.total_assets_for_sale),
        (project_is_paused := pt.abi.Bool()).set(project.is_paused),
        (project_initiated_withdrawal := pt.abi.Bool()).set(project.initiated_withdrawal),
        (project_total_assets_sold := pt.abi.Uint64()).set(project.total_assets_sold),
        (project_total_amount_raised := pt.abi.Uint64()).set(project.total_amount_raised),
        (project_amount_withdrawn := pt.abi.Uint64()).set(project.amount_withdrawn),
        (project_vesting_schedule := pt.abi.Uint64()).set(project.vesting_schedule),

        pt.Assert(
            pt.Txn.sender() == project_owner_address.get(),
            comment="Invalid sender."
        ),
        pt.Assert(
            project_total_amount_raised.get() > pt.Int(0),
            comment="Amount raised must be greater than 0."
        ),
        pt.Assert(
            pt.Global.latest_timestamp() > project_claim_timestamp.get(),
            comment="Withdrawal must be after claim period."
        ),

        (abi_launch_vest_fee := pt.abi.Uint64()).set(LAUNCH_VEST_FEE),
        (amount_raised := pt.abi.Uint64()).set(
            calculate_proceeds_after_fee_deduction(
                project_total_amount_raised,
                abi_launch_vest_fee
            )
        ),
        (percentage := pt.abi.Uint64()).set(PERCENTAGE),
        (disburse_amount := pt.abi.Uint64()).set(
            calculate_disbursement(
                amount_raised,
                percentage
            )
        ),
        pt.If(project_initiated_withdrawal.get() == FALSE)
        .Then(
            disburse(disburse_amount, project_owner_address),
            project_initiated_withdrawal.set(TRUE),
            project_amount_withdrawn.set(project_amount_withdrawn.get() + disburse_amount.get())
        )
        .Else(
            pt.Assert(
                pt.Global.latest_timestamp() > project_vesting_schedule.get(),
                comment="Subsequent withdrawal must be after vesting period."
            ),
            pt.Assert(
                project_amount_withdrawn.get() < amount_raised.get(),
                comment="Accumulated withdrawn amount must be less than amount raised."
            ),
            disburse(disburse_amount, project_owner_address),
            project_amount_withdrawn.set(project_amount_withdrawn.get() + disburse_amount.get())
        ),

        project.set(
            project_owner_address,
            project_start_timestamp,
            project_end_timestamp,
            project_claim_timestamp,
            project_asset_id,
            project_image_url,
            project_price_per_asset,
            project_min_investment_per_investor,
            project_max_investment_per_investor,
            project_max_cap,
            project_total_assets_for_sale,
            project_is_paused,
            project_initiated_withdrawal,
            project_total_assets_sold,
            project_total_amount_raised,
            project_amount_withdrawn,
            project_vesting_schedule
        ),
        app.state.pid_to_project[project_id_bytes].set(project)
    )


# noinspection PyTypeChecker
@app.external(authorize=bk.Authorize.only_creator())
def pause_project(project_id: pt.abi.Uint64) -> pt.Expr:
    """
    Allows pausing a project with the specified project ID.

    :param pt.abi.Uint64 project_id: The unique identifier of the project to be paused.
    :rtype: pt.Expr
    """
    project = Project()
    project_id_bytes = pt.Itob(project_id.get())

    return pt.Seq(
        pt.Assert(
            app.state.pid_to_project[project_id_bytes].exists(),
            comment="Invalid project ID."
        ),

        project.decode(app.state.pid_to_project[project_id_bytes].get()),
        (project_owner_address := pt.abi.Address()).set(project.owner_address),
        (project_start_timestamp := pt.abi.Uint64()).set(project.start_timestamp),
        (project_end_timestamp := pt.abi.Uint64()).set(project.end_timestamp),
        (project_claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),
        (project_asset_id := pt.abi.Uint64()).set(project.asset_id),
        (project_image_url := pt.abi.String()).set(project.image_url),
        (project_price_per_asset := pt.abi.Uint64()).set(project.price_per_asset),
        (project_min_investment_per_investor := pt.abi.Uint64()).set(project.min_investment_per_investor),
        (project_max_investment_per_investor := pt.abi.Uint64()).set(project.max_investment_per_investor),
        (project_max_cap := pt.abi.Uint64()).set(project.max_cap),
        (project_total_assets_for_sale := pt.abi.Uint64()).set(project.total_assets_for_sale),
        (project_is_paused := pt.abi.Bool()).set(project.is_paused),
        (project_initiated_withdrawal := pt.abi.Bool()).set(project.initiated_withdrawal),
        (project_total_assets_sold := pt.abi.Uint64()).set(project.total_assets_sold),
        (project_total_amount_raised := pt.abi.Uint64()).set(project.total_amount_raised),
        (project_amount_withdrawn := pt.abi.Uint64()).set(project.amount_withdrawn),
        (project_vesting_schedule := pt.abi.Uint64()).set(project.vesting_schedule),

        pt.Assert(
            project_is_paused.get() == FALSE,
            comment="Project must not be unpaused before trying to pause."
        ),
        project_is_paused.set(TRUE),

        project.set(
            project_owner_address,
            project_start_timestamp,
            project_end_timestamp,
            project_claim_timestamp,
            project_asset_id,
            project_image_url,
            project_price_per_asset,
            project_min_investment_per_investor,
            project_max_investment_per_investor,
            project_max_cap,
            project_total_assets_for_sale,
            project_is_paused,
            project_initiated_withdrawal,
            project_total_assets_sold,
            project_total_amount_raised,
            project_amount_withdrawn,
            project_vesting_schedule
        ),
        app.state.pid_to_project[project_id_bytes].set(project)
    )


# noinspection PyTypeChecker
@app.external(authorize=bk.Authorize.only_creator())
def unpause_project(project_id: pt.abi.Uint64) -> pt.Expr:
    """
    Allows un-pausing a project with the specified project ID.

    :param pt.abi.Uint64 project_id:The unique identifier of the project to be un-paused.
    :rtype: pt.Expr.
    """
    project = Project()
    project_id_bytes = pt.Itob(project_id.get())

    return pt.Seq(
        pt.Assert(
            app.state.pid_to_project[project_id_bytes].exists(),
            comment="Invalid project ID."
        ),

        project.decode(app.state.pid_to_project[project_id_bytes].get()),
        (project_owner_address := pt.abi.Address()).set(project.owner_address),
        (project_start_timestamp := pt.abi.Uint64()).set(project.start_timestamp),
        (project_end_timestamp := pt.abi.Uint64()).set(project.end_timestamp),
        (project_claim_timestamp := pt.abi.Uint64()).set(project.claim_timestamp),
        (project_asset_id := pt.abi.Uint64()).set(project.asset_id),
        (project_image_url := pt.abi.String()).set(project.image_url),
        (project_price_per_asset := pt.abi.Uint64()).set(project.price_per_asset),
        (project_min_investment_per_investor := pt.abi.Uint64()).set(project.min_investment_per_investor),
        (project_max_investment_per_investor := pt.abi.Uint64()).set(project.max_investment_per_investor),
        (project_max_cap := pt.abi.Uint64()).set(project.max_cap),
        (project_total_assets_for_sale := pt.abi.Uint64()).set(project.total_assets_for_sale),
        (project_is_paused := pt.abi.Bool()).set(project.is_paused),
        (project_initiated_withdrawal := pt.abi.Bool()).set(project.initiated_withdrawal),
        (project_total_assets_sold := pt.abi.Uint64()).set(project.total_assets_sold),
        (project_total_amount_raised := pt.abi.Uint64()).set(project.total_amount_raised),
        (project_amount_withdrawn := pt.abi.Uint64()).set(project.amount_withdrawn),
        (project_vesting_schedule := pt.abi.Uint64()).set(project.vesting_schedule),

        pt.Assert(
            project_is_paused.get() == TRUE,
            comment="Project must be paused before attempting to unpause."
        ),
        project_is_paused.set(FALSE),

        project.set(
            project_owner_address,
            project_start_timestamp,
            project_end_timestamp,
            project_claim_timestamp,
            project_asset_id,
            project_image_url,
            project_price_per_asset,
            project_min_investment_per_investor,
            project_max_investment_per_investor,
            project_max_cap,
            project_total_assets_for_sale,
            project_is_paused,
            project_initiated_withdrawal,
            project_total_assets_sold,
            project_total_amount_raised,
            project_amount_withdrawn,
            project_vesting_schedule
        ),
        app.state.pid_to_project[project_id_bytes].set(project)
    )


# noinspection PyTypeChecker
@app.external(authorize=bk.Authorize.only_creator())
def change_launchpad_admin(new_admin_acct: pt.abi.Address) -> pt.Expr:
    """
    Allows changing the admin account for the launchpad.

    :param pt.abi.Address new_admin_acct: The new admin account address.
    :rtype: pt.Expr
    """
    return app.state.admin_acct.set(new_admin_acct.get())


@app.external(read_only=True)
def get_investor(
    investor: pt.abi.Address,
    *,
    output: Investor
) -> pt.Expr:
    """
    Retrieves investor information for the specified investor address and stores it in the output.

    :param pt.abi.Uint64 investor: The Algorand address of the investor to retrieve.
    :param Project output: The object where investor information will be stored.
    :rtype: pt.Expr.
    """
    return app.state.investor_to_project[investor].store_into(output)


@app.external(read_only=True)
def get_project(
    project_id: pt.abi.Uint64,
    *,
    output: Project
) -> pt.Expr:
    """
    Retrieves project information for the specified project ID and stores it in the output.

    :param pt.abi.Uint64 project_id: The unique identifier of the project to retrieve.
    :param Project output: The object where project information will be stored.
    :rtype: pt.Expr
    """
    return app.state.pid_to_project[project_id].store_into(output)
