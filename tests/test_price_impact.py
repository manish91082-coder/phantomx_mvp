from decimal import Decimal

import pytest

from phantomx.price_impact import build_price_impact_evidence
from phantomx.v2 import V2Pool, V2ReserveSnapshot


POOL = V2Pool(
    venue="QuickSwap V2",
    pair="0x" + "11" * 20,
    token0="0x" + "22" * 20,
    token1="0x" + "33" * 20,
    swap_fee_bps=30,
)


def snapshot(reserve0: int = 1_000_000, reserve1: int = 2_000_000) -> V2ReserveSnapshot:
    return V2ReserveSnapshot(
        pool=POOL,
        reserve0=reserve0,
        reserve1=reserve1,
        block_number=100,
    )


def test_price_impact_excludes_swap_fee_and_is_strictly_positive_for_trade():
    evidence = build_price_impact_evidence(snapshot(), 10_000)

    assert evidence.amount_out_without_fee > 0
    assert evidence.amount_out_with_fee < evidence.amount_out_without_fee
    assert evidence.spot_amount_out == Decimal("20000")
    assert evidence.execution_amount_out == Decimal(evidence.amount_out_without_fee)
    assert evidence.price_impact_fraction > Decimal("0")
    assert evidence.price_impact_bps > Decimal("0")


def test_larger_trade_has_greater_price_impact():
    small = build_price_impact_evidence(snapshot(), 1_000)
    large = build_price_impact_evidence(snapshot(), 100_000)

    assert large.price_impact_fraction > small.price_impact_fraction


def test_zero_or_negative_trade_rejected():
    with pytest.raises(ValueError, match="amount_in must be positive"):
        build_price_impact_evidence(snapshot(), 0)
    with pytest.raises(ValueError, match="amount_in must be positive"):
        build_price_impact_evidence(snapshot(), -1)


def test_zero_reserves_rejected():
    bad = snapshot(reserve0=0)
    with pytest.raises(ValueError, match="pool reserves must be positive"):
        build_price_impact_evidence(bad, 1_000)


def test_price_impact_uses_snapshot_block_as_evidence_anchor():
    evidence = build_price_impact_evidence(snapshot(), 10_000)

    assert evidence.pool.block_number == 100
    assert evidence.pool.pool.venue == "QuickSwap V2"
