from decimal import Decimal

import pytest

from phantomx.slippage import SlippageReference, build_slippage_evidence


REFERENCE = SlippageReference(
    source="reference_venue:QuickSwap V2",
    chain_id=137,
    observed_block=100,
    amount_in=10_000,
    amount_out=19_500,
    asset_out="0x" + "33" * 20,
)


def test_underperformance_is_measured_against_external_reference():
    evidence = build_slippage_evidence(
        REFERENCE,
        execution_amount_in=10_000,
        execution_amount_out=19_305,
        execution_chain_id=137,
        execution_observed_block=100,
    )

    assert evidence.slippage_fraction == Decimal("0.01")
    assert evidence.slippage_bps == Decimal("100.000000")


def test_execution_improvement_is_zero_adverse_slippage():
    evidence = build_slippage_evidence(
        REFERENCE,
        execution_amount_in=10_000,
        execution_amount_out=20_000,
        execution_chain_id=137,
        execution_observed_block=100,
    )

    assert evidence.slippage_fraction == Decimal("0")
    assert evidence.slippage_bps == Decimal("0.000000")


def test_reference_metadata_is_preserved():
    evidence = build_slippage_evidence(
        REFERENCE,
        execution_amount_in=10_000,
        execution_amount_out=19_500,
        execution_chain_id=137,
        execution_observed_block=100,
    )

    assert evidence.reference.source == "reference_venue:QuickSwap V2"
    assert evidence.reference.chain_id == 137
    assert evidence.reference.observed_block == 100
    assert evidence.reference.asset_out == "0x" + "33" * 20


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("execution_amount_in", 0, "execution amount_in must be positive"),
        ("execution_amount_out", -1, "execution amount_out must be non-negative"),
    ],
)
def test_invalid_execution_values_rejected(field, value, message):
    kwargs = {
        "execution_amount_in": 10_000,
        "execution_amount_out": 19_500,
        "execution_chain_id": 137,
        "execution_observed_block": 100,
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=message):
        build_slippage_evidence(REFERENCE, **kwargs)


def test_mismatched_chain_block_or_input_rejected():
    with pytest.raises(ValueError, match="chain_id must match"):
        build_slippage_evidence(
            REFERENCE,
            execution_amount_in=10_000,
            execution_amount_out=19_500,
            execution_chain_id=1,
            execution_observed_block=100,
        )

    with pytest.raises(ValueError, match="observed_block must match"):
        build_slippage_evidence(
            REFERENCE,
            execution_amount_in=10_000,
            execution_amount_out=19_500,
            execution_chain_id=137,
            execution_observed_block=101,
        )

    with pytest.raises(ValueError, match="amount_in must match"):
        build_slippage_evidence(
            REFERENCE,
            execution_amount_in=9_999,
            execution_amount_out=19_500,
            execution_chain_id=137,
            execution_observed_block=100,
        )


def test_reference_validation_rejects_missing_or_invalid_anchor():
    with pytest.raises(ValueError, match="reference source must be non-empty"):
        SlippageReference(
            source="",
            chain_id=137,
            observed_block=100,
            amount_in=10_000,
            amount_out=19_500,
            asset_out="0x" + "33" * 20,
        )

    with pytest.raises(ValueError, match="reference amount_out must be positive"):
        SlippageReference(
            source="reference_venue:QuickSwap V2",
            chain_id=137,
            observed_block=100,
            amount_in=10_000,
            amount_out=0,
            asset_out="0x" + "33" * 20,
        )
