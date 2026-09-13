from decimal import Decimal

import pytest

from phantomx.costs import FlashFeeQuote, GasQuote, RuntimeEconomicCosts, build_economic_inputs


def test_runtime_costs_are_forwarded_without_fallbacks():
    costs = RuntimeEconomicCosts(
        flash_fee_usd=Decimal("0.07"),
        swap_fee_usd=Decimal("0.20"),
        gas_usd=Decimal("0.11"),
        slippage_usd=Decimal("0.06"),
        price_impact_usd=Decimal("0.04"),
        mev_buffer_usd=Decimal("0.09"),
        other_costs_usd=Decimal("0.02"),
        swap_fee_embedded=True,
    )
    inputs = build_economic_inputs(
        gross_output_usd=Decimal("101.50"),
        principal_usd=Decimal("100.00"),
        costs=costs,
    )
    assert inputs.flash_fee_usd == Decimal("0.07")
    assert inputs.gas_usd == Decimal("0.11")
    assert inputs.slippage_usd == Decimal("0.06")
    assert inputs.conservative_net_profit_usd() == Decimal("1.11")


def test_non_embedded_swap_fee_is_included_once():
    costs = RuntimeEconomicCosts(
        flash_fee_usd=Decimal("0.05"),
        swap_fee_usd=Decimal("0.30"),
        gas_usd=Decimal("0.10"),
        slippage_usd=Decimal("0.05"),
        price_impact_usd=Decimal("0.05"),
        mev_buffer_usd=Decimal("0.05"),
        other_costs_usd=Decimal("0.00"),
        swap_fee_embedded=False,
    )
    inputs = build_economic_inputs(Decimal("101.20"), Decimal("100.00"), costs)
    assert inputs.conservative_costs_usd() == Decimal("0.60")
    assert inputs.conservative_net_profit_usd() == Decimal("0.60")


def test_flash_fee_quote_requires_provider():
    quote = FlashFeeQuote(Decimal("1000"), Decimal("0.05"), "Balancer Vault")
    assert quote.provider == "Balancer Vault"
    with pytest.raises(ValueError):
        FlashFeeQuote(Decimal("1000"), Decimal("0.05"), "   ")


def test_gas_quote_derives_expected_wei_exactly():
    quote = GasQuote(
        gas_limit=210_000,
        gas_price_wei=30_000_000_000,
        native_usd=Decimal("0.50"),
        gas_usd=Decimal("0.00315"),
    )
    assert quote.expected_wei == 6_300_000_000_000_000


def test_runtime_costs_reject_nan_and_negative_values():
    with pytest.raises(ValueError):
        RuntimeEconomicCosts(
            flash_fee_usd=Decimal("NaN"),
            swap_fee_usd=Decimal("0"),
            gas_usd=Decimal("0"),
            slippage_usd=Decimal("0"),
            price_impact_usd=Decimal("0"),
            mev_buffer_usd=Decimal("0"),
        )
    with pytest.raises(ValueError):
        RuntimeEconomicCosts(
            flash_fee_usd=Decimal("-0.01"),
            swap_fee_usd=Decimal("0"),
            gas_usd=Decimal("0"),
            slippage_usd=Decimal("0"),
            price_impact_usd=Decimal("0"),
            mev_buffer_usd=Decimal("0"),
        )
