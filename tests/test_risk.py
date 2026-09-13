from decimal import Decimal

import pytest

from phantomx.risk import build_risk_buffer_evidence


def test_risk_buffer_is_exactly_derived_from_explicit_policy():
    evidence = build_risk_buffer_evidence(
        chain_id=137,
        observed_block=500,
        head_block=500,
        notional_usd=Decimal("1000"),
        buffer_bps=Decimal("25"),
        source="operator_policy:conservative_v1",
    )

    assert evidence.buffer_usd == Decimal("2.5")
    assert evidence.buffer_bps == Decimal("25")
    assert evidence.source == "operator_policy:conservative_v1"


def test_stale_block_is_rejected():
    with pytest.raises(ValueError, match="anchored to current head"):
        build_risk_buffer_evidence(
            chain_id=137,
            observed_block=499,
            head_block=500,
            notional_usd=Decimal("1000"),
            buffer_bps=Decimal("25"),
            source="operator_policy:conservative_v1",
        )


def test_zero_buffer_is_rejected():
    with pytest.raises(ValueError, match="between 1 and 10000"):
        build_risk_buffer_evidence(
            chain_id=137,
            observed_block=500,
            head_block=500,
            notional_usd=Decimal("1000"),
            buffer_bps=Decimal("0"),
            source="operator_policy:conservative_v1",
        )


def test_missing_source_is_rejected():
    with pytest.raises(ValueError, match="source must be non-empty"):
        build_risk_buffer_evidence(
            chain_id=137,
            observed_block=500,
            head_block=500,
            notional_usd=Decimal("1000"),
            buffer_bps=Decimal("25"),
            source=" ",
        )


def test_wrong_chain_is_rejected():
    with pytest.raises(ValueError, match="unsupported chain_id"):
        build_risk_buffer_evidence(
            chain_id=1,
            observed_block=500,
            head_block=500,
            notional_usd=Decimal("1000"),
            buffer_bps=Decimal("25"),
            source="operator_policy:conservative_v1",
        )


def test_non_finite_or_non_positive_notional_is_rejected():
    for value in (Decimal("0"), Decimal("-1"), Decimal("NaN")):
        with pytest.raises((ValueError, TypeError)):
            build_risk_buffer_evidence(
                chain_id=137,
                observed_block=500,
                head_block=500,
                notional_usd=value,
                buffer_bps=Decimal("25"),
                source="operator_policy:conservative_v1",
            )
