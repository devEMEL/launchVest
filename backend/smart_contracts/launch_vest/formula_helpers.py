import pyteal as pt


def calculate_project_max_cap(
    total_assets_for_sale: pt.abi.Uint64,
    price_per_asset: pt.abi.Uint64,
    *,
    output: pt.abi.Uint64
) -> pt.Expr:
    """
    Calculates the Project max cap.

    :param pt.abi.Uint64 total_assets_for_sale: The total assets available for sale.
    :param pt.abi.Uint64 price_per_asset: Price for each asset.
    :param pt.abi.Uint64 output: The object where the max. cap result will be stored.
    :rtype: pt.Expr.
    """
    return output.set(total_assets_for_sale.get() * price_per_asset.get())


def calculate_allocation_for_investor(
    investment_amount: pt.abi.Uint64,
    price_per_asset: pt.abi.Uint64,
    *,
    output: pt.abi.Uint64
) -> pt.Expr:
    """
    Formula for calculating an investor's asset allocation.

    :param pt.abi.Uint64 investment_amount: The amount of tokens bought in the base token (ALGO).
    :param pt.abi.Uint64 price_per_asset: The price of the IDO Project asset.
    :param pt.abi.Uint64 output: Result output of the computation.
    :return pt.Expr: Calculated asset allocation for an investor.
    """
    return output.set(investment_amount.get() / price_per_asset.get())


def calculate_proceeds_after_fee_deduction(
    proceeds: pt.abi.Uint64,
    launch_vest_fee: pt.abi.Uint64,
    *,
    output: pt.abi.Uint64
) -> pt.Expr:
    """
    Calculates the claimable amount by project owner after fee deduction.

    :param pt.abi.Uint64 proceeds: The total amount raised from the IDO event.
    :param pt.abi.Uint64 launch_vest_fee: Launch Vest percentage for fee charge.
    :param pt.abi.Uint64 output: The object where the amount will be stored.
    :rtype: pt.Expr.
    """
    return output.set(
        proceeds.get() - ((proceeds.get() * launch_vest_fee.get()) / pt.Int(100))
    )
