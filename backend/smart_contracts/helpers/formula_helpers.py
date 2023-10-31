BASE_VALUE = 10


def asset_price_with_decimals(
    asset_price,
    decimals
):
    return asset_price * (BASE_VALUE ** decimals)


def min_buy_per_user_with_decimals(
    asset_price,
    decimals,
    min_buy
):
    return (min_buy / asset_price) * BASE_VALUE ** decimals


def max_buy_per_user_with_decimals(
    asset_price,
    decimals,
    max_buy
):
    return (max_buy / asset_price) * BASE_VALUE ** decimals


def calculate_allocation_for_investor(
    asset_decimal,
    amount_bought,
    asset_price,
):
    return (amount_bought / asset_price) * BASE_VALUE ** asset_decimal


def calculate_whole_number_of_tokens(
    amount_in_tokens,
    asset_decimals,
):
    return amount_in_tokens / (BASE_VALUE ** asset_decimals)


QUARTER_STAKING_PERIOD = 7_884_000
HALF_YEAR_STAKING_PERIOD = 15_768_000
SECONDS_IN_A_YEAR = ANNUAL_STAKING_PERIOD = 31_536_000

DIVISOR = 31_536_000
RATE = 10


def calculate_staking_reward(
    stake_amount,
    staking_duration
):
    assert (staking_duration == QUARTER_STAKING_PERIOD) or (staking_duration == HALF_YEAR_STAKING_PERIOD) or (staking_duration == ANNUAL_STAKING_PERIOD)
    return (stake_amount * RATE * staking_duration) / (100 * SECONDS_IN_A_YEAR)


def calculate_proceeds_after_fee_deduction(
    proceeds,
    launch_vest_fee
):
    return proceeds - ((proceeds * launch_vest_fee) / 100)


def calculate_disbursement(
    total_amount,
    percentage,
):
    return (percentage / 100) * total_amount


proceeds = calculate_proceeds_after_fee_deduction(1, 10)
print(proceeds)

disbursement = calculate_disbursement(proceeds, 10)
print(disbursement)
