from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from .v2 import V2ReserveSnapshot, amount_out_v2

ZERO = Decimal("0")
ONE = Decimal("1")
BPS = Decimal("10_000")


@dataclass(frozen=True)
class PriceImpactEvidence:
    """Deterministic AMM price-impact evidence for one pool snapshot.

    Price impact excludes the explicitly charged V2 swap fee. The benchmark is
    the pool's instantaneous reserve ratio, while the executable comparison
    uses AMM curve math without fee drag.
    """

    pool: V2ReserveSnapshot
    amount_in: int
    amount_out_with_fee: int
    amount_out_without_fee: int
    spot_amount_out: Decimal
    execution_amount_out: Decimal
    price_impact_fraction: Decimal
    price_impact_bps: Decimal


def build_price_impact_evidence(
    snapshot: V2ReserveSnapshot,
    amount_in: int,
) -> PriceImpactEvidence:
    if amount_in <= 0:
        raise ValueError("amount_in must be positive")
    if snapshot.reserve0 <= 0 or snapshot.reserve1 <= 0:
        raise ValueError("pool reserves must be positive")

    reserve_in = snapshot.reserve0
    reserve_out = snapshot.reserve1

    # Spot benchmark is the instantaneous reserve ratio with no curve impact.
    spot_amount_out = Decimal(amount_in) * Decimal(reserve_out) / Decimal(reserve_in)

    # Remove fee drag while retaining the constant-product curve effect.
    amount_out_without_fee = amount_out_v2(
        amount_in,
        reserve_in,
        reserve_out,
        fee_bps=0,
    )
    if amount_out_without_fee <= 0 or spot_amount_out <= ZERO:
        raise ValueError("unable to establish positive price-impact benchmark")

    execution_amount_out = Decimal(amount_out_without_fee)
    impact_fraction = ONE - (execution_amount_out / spot_amount_out)
    if impact_fraction < ZERO:
        raise ValueError("computed negative price impact")

    price_impact_bps = (impact_fraction * BPS).quantize(
        Decimal("0.000001"), rounding=ROUND_DOWN
    )

    amount_out_with_fee = amount_out_v2(
        amount_in,
        reserve_in,
        reserve_out,
        fee_bps=snapshot.pool.swap_fee_bps,
    )

    return PriceImpactEvidence(
        pool=snapshot,
        amount_in=amount_in,
        amount_out_with_fee=amount_out_with_fee,
        amount_out_without_fee=amount_out_without_fee,
        spot_amount_out=spot_amount_out,
        execution_amount_out=execution_amount_out,
        price_impact_fraction=impact_fraction,
        price_impact_bps=price_impact_bps,
    )
