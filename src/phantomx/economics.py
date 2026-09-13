from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


ZERO = Decimal("0")


class GateStatus(str, Enum):
    GREEN = "GREEN"
    RED = "RED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class EconomicInputs:
    """Conservative authorization inputs for a quoted round trip.

    The V2 quote engine's returned amount already reflects AMM swap fees.
    `swap_fee_usd` therefore remains an audit-attribution field and is charged
    separately only when `swap_fee_embedded` is False.
    """

    gross_output_usd: Decimal
    principal_usd: Decimal
    flash_fee_usd: Decimal
    swap_fee_usd: Decimal
    gas_usd: Decimal
    slippage_usd: Decimal
    price_impact_usd: Decimal
    mev_buffer_usd: Decimal
    other_costs_usd: Decimal
    swap_fee_embedded: bool = True

    def __post_init__(self) -> None:
        for name in (
            "gross_output_usd",
            "principal_usd",
            "flash_fee_usd",
            "swap_fee_usd",
            "gas_usd",
            "slippage_usd",
            "price_impact_usd",
            "mev_buffer_usd",
            "other_costs_usd",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{name} must be Decimal")
            if not value.is_finite():
                raise ValueError(f"{name} must be finite")
            if value < ZERO:
                raise ValueError(f"{name} must be non-negative")

    def conservative_costs_usd(self) -> Decimal:
        explicit_costs = (
            self.flash_fee_usd
            + self.gas_usd
            + self.slippage_usd
            + self.price_impact_usd
            + self.mev_buffer_usd
            + self.other_costs_usd
        )
        return explicit_costs if self.swap_fee_embedded else explicit_costs + self.swap_fee_usd

    def conservative_net_profit_usd(self) -> Decimal:
        return self.gross_output_usd - self.principal_usd - self.conservative_costs_usd()


def economic_gate(
    inputs: EconomicInputs,
    minimum_profit_usd: Decimal = Decimal("0.50"),
) -> GateStatus:
    if not isinstance(minimum_profit_usd, Decimal):
        raise TypeError("minimum_profit_usd must be Decimal")
    if not minimum_profit_usd.is_finite() or minimum_profit_usd < ZERO:
        raise ValueError("minimum_profit_usd must be finite and non-negative")
    return (
        GateStatus.GREEN
        if inputs.conservative_net_profit_usd() > minimum_profit_usd
        else GateStatus.BLOCKED
    )
