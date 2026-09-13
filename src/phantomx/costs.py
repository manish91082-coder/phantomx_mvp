from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .economics import EconomicInputs


ZERO = Decimal("0")


@dataclass(frozen=True)
class RuntimeEconomicCosts:
    """Runtime-supplied conservative costs for one candidate execution.

    All monetary values are already normalized to USD by the caller. No
    default cost is invented here. Missing or unverified values must be
    rejected by the caller before authorization.
    """

    flash_fee_usd: Decimal
    swap_fee_usd: Decimal
    gas_usd: Decimal
    slippage_usd: Decimal
    price_impact_usd: Decimal
    mev_buffer_usd: Decimal
    other_costs_usd: Decimal = ZERO
    swap_fee_embedded: bool = True

    def __post_init__(self) -> None:
        for name in (
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
            if not value.is_finite() or value < ZERO:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True)
class GasQuote:
    """Gas cost evidence converted to USD by an upstream runtime adapter."""

    gas_limit: int
    gas_price_wei: int
    native_usd: Decimal
    gas_usd: Decimal

    def __post_init__(self) -> None:
        if self.gas_limit <= 0 or self.gas_price_wei <= 0:
            raise ValueError("gas_limit and gas_price_wei must be positive")
        if not self.native_usd.is_finite() or self.native_usd <= ZERO:
            raise ValueError("native_usd must be finite and positive")
        if not self.gas_usd.is_finite() or self.gas_usd < ZERO:
            raise ValueError("gas_usd must be finite and non-negative")

    @property
    def expected_wei(self) -> int:
        return self.gas_limit * self.gas_price_wei


@dataclass(frozen=True)
class FlashFeeQuote:
    """Exact flash-loan fee evidence for a known borrowed principal."""

    principal_usd: Decimal
    flash_fee_usd: Decimal
    provider: str

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must be non-empty")
        if not self.principal_usd.is_finite() or self.principal_usd <= ZERO:
            raise ValueError("principal_usd must be finite and positive")
        if not self.flash_fee_usd.is_finite() or self.flash_fee_usd < ZERO:
            raise ValueError("flash_fee_usd must be finite and non-negative")


def build_economic_inputs(
    gross_output_usd: Decimal,
    principal_usd: Decimal,
    costs: RuntimeEconomicCosts,
) -> EconomicInputs:
    """Convert a runtime cost snapshot into the deterministic gate input.

    The function deliberately performs no estimation or fallback. The caller
    is responsible for obtaining and independently validating each runtime
    observation. Missing evidence must therefore prevent construction.
    """

    return EconomicInputs(
        gross_output_usd=gross_output_usd,
        principal_usd=principal_usd,
        flash_fee_usd=costs.flash_fee_usd,
        swap_fee_usd=costs.swap_fee_usd,
        gas_usd=costs.gas_usd,
        slippage_usd=costs.slippage_usd,
        price_impact_usd=costs.price_impact_usd,
        mev_buffer_usd=costs.mev_buffer_usd,
        other_costs_usd=costs.other_costs_usd,
        swap_fee_embedded=costs.swap_fee_embedded,
    )
