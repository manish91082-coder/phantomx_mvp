from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .chain_rpc import ChainRpcAdapter, RpcError, RpcTransport, decode_uint256
from .costs import FlashFeeQuote


ZERO = Decimal("0")
BPS_DENOMINATOR = Decimal("10_000")
AAVE_V3_FLASHLOAN_PREMIUM_TOTAL_SELECTOR = "0x074b2e43"


@dataclass(frozen=True)
class FlashFeeEvidence:
    """Read-only, block-anchored flash-loan fee evidence."""

    quote: FlashFeeQuote
    provider: str
    pool: str
    chain_id: int
    observed_block: int
    premium_bps: int


class AaveV3PolygonFlashFeeAdapter:
    """Read Aave V3's live flash-loan premium on Polygon.

    This adapter only performs ``eth_getCode``, chain/head, and ``eth_call``
    reads. The Pool address is injected from trusted deployment configuration;
    this module does not guess addresses or fee values.
    """

    def __init__(self, transport: RpcTransport, pool_address: str, expected_chain_id: int = 137) -> None:
        if expected_chain_id <= 0:
            raise ValueError("expected_chain_id must be positive")
        self._rpc = ChainRpcAdapter(transport)
        self._pool = pool_address
        self._expected_chain_id = expected_chain_id

    def quote(self, principal_usd: Decimal) -> FlashFeeEvidence:
        if not isinstance(principal_usd, Decimal):
            raise TypeError("principal_usd must be Decimal")
        if not principal_usd.is_finite() or principal_usd <= ZERO:
            raise ValueError("principal_usd must be finite and positive")

        head = self._rpc.head()
        if head.chain_id != self._expected_chain_id:
            raise RpcError(
                f"unexpected chain id: expected {self._expected_chain_id}, got {head.chain_id}"
            )

        code = self._rpc.code_at(self._pool, block_tag=hex(head.block_number))
        if not code:
            raise RpcError("Aave V3 Pool address has no deployed code at observation block")

        raw = self._rpc.eth_call(
            self._pool,
            AAVE_V3_FLASHLOAN_PREMIUM_TOTAL_SELECTOR,
            block_tag=hex(head.block_number),
        )
        premium_bps = decode_uint256(raw)
        if premium_bps < 0 or premium_bps > 10_000:
            raise RpcError("Aave V3 flash-loan premium is outside valid bps range")

        fee_usd = principal_usd * Decimal(premium_bps) / BPS_DENOMINATOR
        quote = FlashFeeQuote(
            principal_usd=principal_usd,
            flash_fee_usd=fee_usd,
            provider="Aave V3",
        )
        return FlashFeeEvidence(
            quote=quote,
            provider="Aave V3",
            pool=self._pool,
            chain_id=head.chain_id,
            observed_block=head.block_number,
            premium_bps=premium_bps,
        )
