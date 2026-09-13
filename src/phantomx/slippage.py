from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

ZERO = Decimal("0")
ONE = Decimal("1")
BPS = Decimal("10_000")


@dataclass(frozen=True)
class SlippageReference:
    """Externally anchored expected output for one coherent observation."""

    source: str
    chain_id: int
    observed_block: int
    amount_in: int
    amount_out: int
    asset_out: str

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("reference source must be non-empty")
        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")
        if self.observed_block < 0:
            raise ValueError("observed_block must be non-negative")
        if self.amount_in <= 0:
            raise ValueError("reference amount_in must be positive")
        if self.amount_out <= 0:
            raise ValueError("reference amount_out must be positive")
        if not self.asset_out.strip():
            raise ValueError("asset_out must be non-empty")


@dataclass(frozen=True)
class SlippageEvidence:
    """Deterministic adverse-slippage evidence against an external reference.

    Slippage is measured only when execution underperforms the anchored
    reference output. Positive execution improvement is recorded as zero
    adverse slippage rather than being treated as a loss.
    """

    reference: SlippageReference
    execution_amount_in: int
    execution_amount_out: int
    slippage_fraction: Decimal
    slippage_bps: Decimal


def build_slippage_evidence(
    reference: SlippageReference,
    *,
    execution_amount_in: int,
    execution_amount_out: int,
    execution_chain_id: int,
    execution_observed_block: int,
) -> SlippageEvidence:
    """Compare executable output with a caller-supplied external reference.

    No default percentage, guessed tolerance, stale-block substitution, or
    fallback price source is permitted.
    """
    if execution_amount_in <= 0:
        raise ValueError("execution amount_in must be positive")
    if execution_amount_out < 0:
        raise ValueError("execution amount_out must be non-negative")
    if execution_chain_id <= 0:
        raise ValueError("execution chain_id must be positive")
    if execution_observed_block < 0:
        raise ValueError("execution_observed_block must be non-negative")
    if execution_chain_id != reference.chain_id:
        raise ValueError("reference and execution chain_id must match")
    if execution_observed_block != reference.observed_block:
        raise ValueError("reference and execution observed_block must match")
    if execution_amount_in != reference.amount_in:
        raise ValueError("reference and execution amount_in must match")

    execution = Decimal(execution_amount_out)
    expected = Decimal(reference.amount_out)
    adverse_fraction = ONE - (execution / expected)
    if adverse_fraction < ZERO:
        adverse_fraction = ZERO

    slippage_bps = (adverse_fraction * BPS).quantize(
        Decimal("0.000001"), rounding=ROUND_DOWN
    )

    return SlippageEvidence(
        reference=reference,
        execution_amount_in=execution_amount_in,
        execution_amount_out=execution_amount_out,
        slippage_fraction=adverse_fraction,
        slippage_bps=slippage_bps,
    )
