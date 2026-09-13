from decimal import Decimal

import pytest

from phantomx.economics import EconomicInputs, GateStatus, economic_gate


COMMON = dict(
    principal_usd=Decimal("100.00"),
    flash_fee_usd=Decimal("0.05"),
    gas_usd=Decimal("0.20"),
    slippage_usd=Decimal("0.10"),
    price_impact_usd=Decimal("0.10"),
    mev_buffer_usd=Decimal("0.10"),
    other_costs_usd=Decimal("0.00"),
)


def test_non_positive_trade_is_blocked():
    inputs = EconomicInputs(
        gross_output_usd=Decimal("100.00"),
        swap_fee_usd=Decimal("0.10"),
        **COMMON,
    )
    assert inputs.conservative_net_profit_usd() < 0
    assert economic_gate(inputs) is GateStatus.BLOCKED


def test_embedded_swap_fee_is_not_double_counted():
    # The V2 amount_out quote already includes AMM swap fees. Keep the fee
    # visible for attribution, but do not subtract it a second time.
    inputs = EconomicInputs(
        gross_output_usd=Decimal("100.96"),
        swap_fee_usd=Decimal("0.30"),
        **COMMON,
    )
    assert inputs.conservative_net_profit_usd() == Decimal("0.41")
    assert economic_gate(inputs) is GateStatus.BLOCKED


def test_non_embedded_swap_fee_is_charged_once():
    inputs = EconomicInputs(
        gross_output_usd=Decimal("101.11"),
        swap_fee_usd=Decimal("0.30"),
        swap_fee_embedded=False,
        **COMMON,
    )
    assert inputs.conservative_net_profit_usd() == Decimal("0.26")
    assert inputs.conservative_costs_usd() == Decimal("0.85")


def test_exact_half_dollar_threshold_is_blocked():
    inputs = EconomicInputs(
        gross_output_usd=Decimal("101.05"),
        swap_fee_usd=Decimal("0.00"),
        **COMMON,
    )
    assert inputs.conservative_net_profit_usd() == Decimal("0.50")
    assert economic_gate(inputs) is GateStatus.BLOCKED


def test_profit_must_strictly_exceed_threshold():
    inputs = EconomicInputs(
        gross_output_usd=Decimal("101.051"),
        swap_fee_usd=Decimal("0.00"),
        **COMMON,
    )
    assert inputs.conservative_net_profit_usd() == Decimal("0.501")
    assert economic_gate(inputs) is GateStatus.GREEN


def test_negative_or_non_finite_costs_are_rejected():
    with pytest.raises(ValueError):
        EconomicInputs(
            gross_output_usd=Decimal("101"),
            swap_fee_usd=Decimal("-0.01"),
            **COMMON,
        )
    with pytest.raises(ValueError):
        EconomicInputs(
            gross_output_usd=Decimal("NaN"),
            swap_fee_usd=Decimal("0"),
            **COMMON,
        )
