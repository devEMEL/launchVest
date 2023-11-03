import pyteal as pt


@pt.Subroutine(pt.TealType.uint64)
def calculate_project_max_cap(
    total_assets_for_sale: pt.abi.Uint64,
    price_per_asset: pt.abi.Uint64,
) -> pt.Expr:
    """
    Calculates the Project max cap.

    Arguments must be passed in their order, since this is ``pt.Subroutine`` which only accepts positional args.

    :param pt.abi.Uint64 total_assets_for_sale: The total assets available for sale.
    :param pt.abi.Uint64 price_per_asset: Price for each asset.
    :rtype: pt.Expr.
    """
    return total_assets_for_sale.get() * price_per_asset.get()


# noinspection PyTypeChecker
@pt.Subroutine(pt.TealType.uint64)
def calculate_allocation_for_investor(
    investment_amount: pt.abi.Uint64,
    price_per_asset: pt.abi.Uint64,
) -> pt.Expr:
    """
    Formula for calculating an investor's asset allocation.

    Arguments must be passed in their order, since this is ``pt.Subroutine`` which only accepts positional args.

    :param pt.abi.Uint64 investment_amount: The amount of tokens bought in the base token (ALGO).
    :param pt.abi.Uint64 price_per_asset: The price of the IDO Project asset.
    :return pt.Expr: Calculated asset allocation for an investor.
    """
    return pt.Seq(
        pt.Assert(
            investment_amount.get() >= price_per_asset.get(),
            comment="Investment amount cannot be lesser than asset price"
        ),
        pt.Return(investment_amount.get() / price_per_asset.get())
    )


@pt.Subroutine(pt.TealType.uint64)
def calculate_proceeds_after_fee_deduction(
    proceeds: pt.abi.Uint64,
    launch_vest_fee: pt.abi.Uint64
) -> pt.Expr:
    """
    Calculates the claimable amount by project owner after fee deduction.

    Arguments must be passed in their order, since this is ``pt.Subroutine`` which only accepts positional args.

    :param pt.abi.Uint64 proceeds: The total amount raised from the IDO event.
    :param pt.abi.Uint64 launch_vest_fee: Launch Vest percentage for fee charge.
    :rtype: pt.Expr.
    """
    return proceeds.get() - ((proceeds.get() * launch_vest_fee.get()) / pt.Int(100))


# noinspection PyTypeChecker
@pt.Subroutine(pt.TealType.uint64)
def calculate_disbursement(
    total_amount: pt.abi.Uint64,
    percentage: pt.abi.Uint64
) -> pt.Expr:
    """
    Calculates the amount to be disbursed to the project owner.

    Arguments must be passed in their order, since this is ``pt.Subroutine`` which only accepts positional args.

    :param total_amount: The total amount raised.
    :param percentage: The percentage to payout after each vesting period.
    :rtype pt.Expr:
    """
    return pt.Seq(
        pt.Assert(percentage.get() > pt.Int(0), percentage.get() <= pt.Int(100)),
        pt.Return((percentage.get() * total_amount.get()) / pt.Int(100))
    )
