import beaker as bk
import pyteal as pt

from beaker.consts import FALSE, TRUE
from beaker.lib.storage import BoxMapping


class Property(pt.abi.NamedTuple):
    """
    Represents a property, extends ``pt.abi.NamedTuple``.

    """
    owner_address: pt.abi.Field[pt.abi.Address]
    id: pt.abi.Field[pt.abi.Uint64]
    image_url: pt.abi.Field[pt.abi.String]
    amount: pt.abi.Field[pt.abi.Uint64]
    total_supply: pt.abi.Field[pt.abi.Uint64]
    min_investment: pt.abi.Field[pt.abi.Uint64]
    max_investment: pt.abi.Field[pt.abi.Uint64]
    soft_cap: pt.abi.Field[pt.abi.Uint64]
    hard_cap: pt.abi.Field[pt.abi.Uint64]
