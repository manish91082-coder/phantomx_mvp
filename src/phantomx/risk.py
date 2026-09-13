from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

ZERO = Decimal("0")
BPS_DENOMINATOR = Decimal("10_000")
MIN_BUFFER_BPS = Decimal("1")
MAX_BUFFER_BPS = Decimal("10_000")
POLYGON_CHAIN_ID = 137


@dataclass(frozen=True)
class RiskBufferEvidence:
    """Auditable conservative policy-floor evidence.

    This is an explicit runtime policy floor, not a predictive MEV oracle.
    A non-zero, source-labelled basis-point floor is required and must be
    anchored to the same observed head block as the candidate evidence.
    """

    chain_id: int
    observed_block: int
    head_block: int
    notional_usd: Decimal
    buffer_bps: Decimal
    buffer_usd: Decimal
    source: str

    def __post_init__(self) -> None:
        if self.chain_id != POLYGON_CHAIN_ID:
            raise ValueError("unsupported chain_id")
        if self.observed_block <= 0 or self.head_block <= 0:
            raise ValueError("block numbers must be positive")
        if self.observed_block != self.head_block:
            raise ValueError("risk evidence must be anchored to current head")
        if not self.notional_usd.is_finite() or self.notional_usd <= ZERO:
            raise ValueError("notional_usd must be finite and positive")
        if not self.buffer_bps.is_finite() or not (
            MIN_BUFFER_BPS <= self.buffer_bps <= MAX_BUFFER_BPS
        ):
            raise ValueError("buffer_bps must be between 1 and 10000")
        if not self.buffer_usd.is_finite() or self.buffer_usd <= ZERO:
            raise ValueError("buffer_usd must be finite and positive")
        if not self.source.strip():
            raise ValueError("source must be non-empty")


def build_risk_buffer_evidence(
    *,
    chain_id: int,
    observed_block: int,
    head_block: int,
    notional_usd: Decimal,
    buffer_bps: Decimal,
    source: str,
) -> RiskBufferEvidence:
    """Build fail-closed conservative risk-buffer evidence.

    The buffer is exactly ``notional_usd * buffer_bps / 10_000``. No default
    percentage, oracle guess, or fallback is introduced. The caller must
    provide a positive policy floor and an explicit provenance label.
    """

    if not isinstance(notional_usd, Decimal) or not isinstance(buffer_bps, Decimal):
        raise TypeError("notional_usd and buffer_bps must be Decimal")

    buffer_usd = (notional_usd * buffer_bps) / BPS_DENOMINATOR
    return RiskBufferEvidence(
        chain_id=chain_id,
        observed_block=observed_block,
        head_block=head_block,
        notional_usd=notional_usd,
        buffer_bps=buffer_bps,
        buffer_usd=buffer_usd,
        source=source,
    )
