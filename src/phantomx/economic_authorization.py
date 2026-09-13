from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .costs import RuntimeEconomicCosts, build_economic_inputs
from .economics import EconomicInputs, GateStatus, economic_gate
from .flash_fee import FlashFeeEvidence
from .price_impact import PriceImpactEvidence
from .risk import RiskBufferEvidence
from .routes import DirectArbQuote
from .runtime_evidence import GasEvidence
from .slippage import SlippageEvidence

POLYGON_CHAIN_ID = 137


@dataclass(frozen=True)
class EconomicAuthorizationEvidence:
    """Single coherent evidence bundle for deterministic V2 authorization."""

    quote: DirectArbQuote
    gas: GasEvidence
    flash_fee: FlashFeeEvidence
    price_impact: PriceImpactEvidence
    slippage: SlippageEvidence
    risk_buffer: RiskBufferEvidence
    inputs: EconomicInputs
    status: GateStatus


def authorize_v2_candidate(
    *,
    quote: DirectArbQuote,
    gross_output_usd: Decimal,
    principal_usd: Decimal,
    costs: RuntimeEconomicCosts,
    gas: GasEvidence,
    flash_fee: FlashFeeEvidence,
    price_impact: PriceImpactEvidence,
    slippage: SlippageEvidence,
    risk_buffer: RiskBufferEvidence,
    minimum_profit_usd: Decimal = Decimal("0.50"),
) -> EconomicAuthorizationEvidence:
    """Authorize only a fully coherent V2 candidate evidence bundle.

    AI-generated opportunity selection is not sufficient. Every evidence
    component must identify Polygon and share the quoted route's block. The
    deterministic economic gate remains the sole authorization decision.
    """

    _require_decimal(gross_output_usd, "gross_output_usd")
    _require_decimal(principal_usd, "principal_usd")
    _require_block_coherence(quote, gas, flash_fee, price_impact, slippage, risk_buffer)
    if flash_fee.quote.principal_usd != principal_usd:
        raise ValueError("flash-fee principal must match economic principal")
    if risk_buffer.notional_usd != principal_usd:
        raise ValueError("risk-buffer notional must match economic principal")
    if slippage.execution_amount_in != quote.input_amount:
        raise ValueError("slippage input must match route input")
    if slippage.reference.asset_out.strip() != quote.pair.token_b.address.strip():
        raise ValueError("slippage asset_out must match candidate intermediate asset")
    if price_impact.amount_in != quote.input_amount:
        raise ValueError("price-impact input must match route input")

    inputs = build_economic_inputs(gross_output_usd, principal_usd, costs)
    status = economic_gate(inputs, minimum_profit_usd)
    return EconomicAuthorizationEvidence(
        quote=quote,
        gas=gas,
        flash_fee=flash_fee,
        price_impact=price_impact,
        slippage=slippage,
        risk_buffer=risk_buffer,
        inputs=inputs,
        status=status,
    )


def _require_block_coherence(
    quote: DirectArbQuote,
    gas: GasEvidence,
    flash_fee: FlashFeeEvidence,
    price_impact: PriceImpactEvidence,
    slippage: SlippageEvidence,
    risk_buffer: RiskBufferEvidence,
) -> None:
    block = quote.block_number
    if gas.chain_id != POLYGON_CHAIN_ID or flash_fee.chain_id != POLYGON_CHAIN_ID:
        raise ValueError("runtime economic evidence must be on Polygon")
    if gas.observed_block != block or flash_fee.observed_block != block:
        raise ValueError("gas and flash-fee evidence must match route block")
    if price_impact.pool.block_number != block:
        raise ValueError("price-impact evidence must match route block")
    if slippage.reference.chain_id != POLYGON_CHAIN_ID:
        raise ValueError("slippage reference must be on Polygon")
    if slippage.reference.observed_block != block:
        raise ValueError("slippage evidence must match route block")
    if risk_buffer.chain_id != POLYGON_CHAIN_ID or risk_buffer.observed_block != block:
        raise ValueError("risk evidence must match route block")


def _require_decimal(value: Decimal, name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal")
    if not value.is_finite() or value < Decimal("0"):
        raise ValueError(f"{name} must be finite and non-negative")
