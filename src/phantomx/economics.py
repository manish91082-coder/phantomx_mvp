from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class GateStatus(str, Enum):
    GREEN = "GREEN"
    RED = "RED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class EconomicInputs:
    """Economic inputs for a V2 round trip.

    gross_output_usd is the quoted return after AMM swap fees have already
    been applied by the V2 quote engine. swap_fee_usd is retained for audit
    attribution and is only charged separately when swap_fee_embedded=False.
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
            if value < 0:
                raise ValueError(f"{name} must be non-negative")

    def conservative_costs_usd(self) -> Decimal:
        explicit = (
            self.flash_fee_usd
            + self.gas_usd
            + self.slippage_usd
            + self.price_impact_usd
            + self.mev_buffer_usd
            + self.other_costs_usd
        )
        # amount_out_v2 already incorporates the AMM swap fee. Do not deduct
        # the same fee a second time in that case.
        return explicit if self.swap_fee_embedded else explicit + self.swap_fee_usd

    def conservative_net_profit_usd(self) -> Decimal:
        return self.gross_output_usd - self.principal_usd - self.conservative_costs_usd()


def economic_gate(
    inputs: EconomicInputs,
    minimum_profit_usd: Decimal = Decimal("0.50"),
) -> GateStatus:
    if not isinstance(minimum_profit_usd, Decimal):
        raise TypeError("minimum_profit_usd must be Decimal")
    if not minimum_profit_usd.is_finite() or minimum_profit_usd < 0:
        raise ValueError("minimum_profit_usd must be finite and non-negative")
    return (
        GateStatus.GREEN
        if inputs.conservative_net_profit_usd() > minimum_profit_usd
        else GateStatus.BLOCKED
    )
