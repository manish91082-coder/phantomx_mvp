from decimal import Decimal

import pytest

from phantomx.costs import RuntimeEconomicCosts
from phantomx.economic_authorization import authorize_v2_candidate
from phantomx.flash_fee import FlashFeeEvidence
from phantomx.price_impact import build_price_impact_evidence
from phantomx.risk import build_risk_buffer_evidence
from phantomx.routes import DirectArbQuote, Direction
from phantomx.runtime_evidence import GasEvidence, UsdPriceObservation
from phantomx.slippage import SlippageEvidence, SlippageReference, build_slippage_evidence
from phantomx.v2 import Token, V2Pool, V2ReserveSnapshot
from phantomx.costs import FlashFeeQuote, GasQuote
from phantomx.market import MarketPair


TOKEN_A = Token("A", "0x" + "11" * 20, 6)
TOKEN_B = Token("B", "0x" + "22" * 20, 6)
PAIR = MarketPair(TOKEN_A, TOKEN_B)
POOL = V2Pool("QuickSwap V2", "0x" + "33" * 20, TOKEN_A.address, TOKEN_B.address, 30)
SNAPSHOT = V2ReserveSnapshot(POOL, 1_000_000, 2_000_000, 500)


def build_bundle():
    quote = DirectArbQuote(
        pair=PAIR,
        buy_pool=SNAPSHOT,
        sell_pool=V2ReserveSnapshot(
            V2Pool("Uniswap V2", "0x" + "44" * 20, TOKEN_A.address, TOKEN_B.address, 30),
            1_100_000,
            2_200_000,
            500,
        ),
        input_amount=10_000,
        intermediate_amount=19_000,
        returned_amount=10_200,
        gross_profit_units=200,
        direction=Direction.BUY_ON_FIRST_SELL_ON_SECOND,
        block_number=500,
    )
    gas_quote = GasQuote(210_000, 1_000_000_000, Decimal("0.50"), Decimal("0.105"))
    gas = GasEvidence(gas_quote, 137, 500, UsdPriceObservation(Decimal("0.50"), "reference", 500))
    flash_quote = FlashFeeQuote(Decimal("100.00"), Decimal("0.09"), "Aave V3")
    flash = FlashFeeEvidence(flash_quote, "Aave V3", "0x" + "55" * 20, 137, 500, 9)
    impact = build_price_impact_evidence(SNAPSHOT, 10_000)
    reference = SlippageReference("external_reference", 137, 500, 10_000, 20_000, TOKEN_B.address)
    slippage = build_slippage_evidence(
        reference,
        execution_amount_in=10_000,
        execution_amount_out=19_900,
        execution_chain_id=137,
        execution_observed_block=500,
    )
    risk = build_risk_buffer_evidence(
        chain_id=137,
        observed_block=500,
        head_block=500,
        notional_usd=Decimal("100.00"),
        buffer_bps=Decimal("25"),
        source="operator_policy:conservative_v1",
    )
    costs = RuntimeEconomicCosts(
        flash_fee_usd=Decimal("0.09"),
        swap_fee_usd=Decimal("0"),
        gas_usd=Decimal("0.105"),
        slippage_usd=Decimal("0.50"),
        price_impact_usd=Decimal("0.20"),
        mev_buffer_usd=risk.buffer_usd,
        other_costs_usd=Decimal("0"),
    )
    return quote, gas, flash, impact, slippage, risk, costs


def test_complete_coherent_bundle_reaches_deterministic_gate():
    quote, gas, flash, impact, slippage, risk, costs = build_bundle()
    result = authorize_v2_candidate(
        quote=quote,
        gross_output_usd=Decimal("101.80"),
        principal_usd=Decimal("100.00"),
        costs=costs,
        gas=gas,
        flash_fee=flash,
        price_impact=impact,
        slippage=slippage,
        risk_buffer=risk,
        minimum_profit_usd=Decimal("0.50"),
    )
    assert result.status.value == "GREEN"


def test_missing_block_coherence_is_fail_closed():
    quote, gas, flash, impact, slippage, risk, costs = build_bundle()
    stale_risk = build_risk_buffer_evidence(
        chain_id=137,
        observed_block=499,
        head_block=499,
        notional_usd=Decimal("100.00"),
        buffer_bps=Decimal("25"),
        source="operator_policy:conservative_v1",
    )
    with pytest.raises(ValueError, match="risk evidence must match route block"):
        authorize_v2_candidate(
            quote=quote,
            gross_output_usd=Decimal("101.80"),
            principal_usd=Decimal("100.00"),
            costs=costs,
            gas=gas,
            flash_fee=flash,
            price_impact=impact,
            slippage=slippage,
            risk_buffer=stale_risk,
        )


def test_negative_economic_result_blocks_even_with_coherent_evidence():
    quote, gas, flash, impact, slippage, risk, costs = build_bundle()
    result = authorize_v2_candidate(
        quote=quote,
        gross_output_usd=Decimal("100.70"),
        principal_usd=Decimal("100.00"),
        costs=costs,
        gas=gas,
        flash_fee=flash,
        price_impact=impact,
        slippage=slippage,
        risk_buffer=risk,
    )
    assert result.status.value == "BLOCKED"


def test_principal_mismatch_is_rejected():
    quote, gas, flash, impact, slippage, risk, costs = build_bundle()
    with pytest.raises(ValueError, match="flash-fee principal"):
        authorize_v2_candidate(
            quote=quote,
            gross_output_usd=Decimal("101.80"),
            principal_usd=Decimal("99.00"),
            costs=costs,
            gas=gas,
            flash_fee=flash,
            price_impact=impact,
            slippage=slippage,
            risk_buffer=risk,
        )
