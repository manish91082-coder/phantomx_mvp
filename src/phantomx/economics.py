from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class GateStatus(str, Enum):
    GREEN = "GREEN"
    RED = "RED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class EconomicInputs:
    gross_output_usd: Decimal
    principal_usd: Decimal
    flash_fee_usd: Decimal
    swap_fee_usd: Decimal
    gas_usd: Decimal
    slippage_usd: Decimal
    price_impact_usd: Decimal
    mev_buffer_usd: Decimal
    other_costs_usd: Decimal

    def conservative_net_profit_usd(self) -> Decimal:
        costs = (
            self.flash_fee_usd
            + self.swap_fee_usd
            + self.gas_usd
            + self.slippage_usd
            + self.price_impact_usd
            + self.mev_buffer_usd
            + self.other_costs_usd
        )
        return self.gross_output_usd - self.principal_usd - costs


def economic_gate(inputs: EconomicInputs, minimum_profit_usd: Decimal = Decimal("0.50")) -> GateStatus:
    return GateStatus.GREEN if inputs.conservative_net_profit_usd() > minimum_profit_usd else GateStatus.BLOCKED
