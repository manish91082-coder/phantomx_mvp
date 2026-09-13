import pytest
from decimal import Decimal

from phantomx.economics import EconomicInputs, GateStatus, economic_gate


def test_non_positive_trade_is_blocked():
    inputs = EconomicInputs(
        gross_output_usd=Decimal("100.00"),
        principal_usd=Decimal("100.00"),
        flash_fee_usd=Decimal("0.05"),
        swap_fee_usd=Decimal("0.10"),
        gas_usd=Decimal("0.20"),
        slippage_usd=Decimal("0.10"),
        price_impact_usd=Decimal("0.10"),
        mev_buffer_usd=Decimal("0.10"),
        other_costs_usd=Decimal("0.00"),
    )
    assert inputs.conservative_net_profit_usd() < 0
    assert economic_gate(inputs) is GateStatus.BLOCKED


def test_profit_must_strictly_exceed_threshold():
    base = dict(
        principal_usd=Decimal("100.00"),
        flash_fee_usd=Decimal("0.05"),
        swap_fee_usd=Decimal("0.05"),
        gas_usd=Decimal("0.05"),
        slippage_usd=Decimal("0.05"),
        price_impact_usd=Decimal("0.05"),
        mev_buffer_usd=Decimal("0.05"),
        other_costs_usd=Decimal("0.00"),
    )
    at_threshold = EconomicInputs(gross_output_usd=Decimal("100.80"), **base)
    above_threshold = EconomicInputs(gross_output_usd=Decimal("100.81"), **base)
    assert economic_gate(at_threshold) is GateStatus.BLOCKED
    assert economic_gate(above_threshold) is GateStatus.GREEN
