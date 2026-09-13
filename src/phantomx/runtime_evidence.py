from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .chain_rpc import ChainRpcAdapter, RpcError, RpcTransport
from .costs import GasQuote


ZERO = Decimal("0")


@dataclass(frozen=True)
class UsdPriceObservation:
    """A caller-supplied, explicitly identified native-token USD observation."""

    usd: Decimal
    source: str
    observed_block: int

    def __post_init__(self) -> None:
        if not isinstance(self.usd, Decimal):
            raise TypeError("usd must be Decimal")
        if not self.usd.is_finite() or self.usd <= ZERO:
            raise ValueError("usd must be finite and positive")
        if not self.source.strip():
            raise ValueError("source must be non-empty")
        if self.observed_block < 0:
            raise ValueError("observed_block must be non-negative")


@dataclass(frozen=True)
class GasEvidence:
    """Auditable read-only gas evidence for one candidate transaction."""

    quote: GasQuote
    chain_id: int
    observed_block: int
    price_observation: UsdPriceObservation


class PolygonGasEvidenceAdapter:
    """Build a read-only Polygon gas quote with block-coherent evidence.

    No signing or broadcast is performed. Gas units come from
    ``eth_estimateGas`` and gas price from ``eth_gasPrice``. Native-token USD
    valuation is injected as an explicit, source-labelled observation; no
    price fallback is invented here.
    """

    def __init__(self, transport: RpcTransport, expected_chain_id: int = 137) -> None:
        if expected_chain_id <= 0:
            raise ValueError("expected_chain_id must be positive")
        self._transport = transport
        self._rpc = ChainRpcAdapter(transport)
        self._expected_chain_id = expected_chain_id

    def quote(
        self,
        transaction: dict[str, Any],
        native_usd: UsdPriceObservation,
    ) -> GasEvidence:
        if not isinstance(transaction, dict) or not transaction:
            raise ValueError("transaction must be a non-empty mapping")
        if not isinstance(native_usd, UsdPriceObservation):
            raise TypeError("native_usd must be a UsdPriceObservation")

        first_head = self._rpc.head()
        if first_head.chain_id != self._expected_chain_id:
            raise RpcError(
                f"unexpected chain id: expected {self._expected_chain_id}, got {first_head.chain_id}"
            )

        estimated_gas = self._estimate_gas(transaction)
        gas_price_wei = self._gas_price()
        second_head = self._rpc.head()

        if second_head.chain_id != first_head.chain_id:
            raise RpcError("chain id changed during gas observation")
        if second_head.block_number != first_head.block_number:
            raise RpcError(
                "Polygon head advanced during gas observation; retry for a same-block evidence snapshot"
            )
        if native_usd.observed_block != first_head.block_number:
            raise RpcError("native USD observation is not aligned to the gas observation block")

        gas_usd = (Decimal(estimated_gas * gas_price_wei) * native_usd.usd) / Decimal(10**18)
        quote = GasQuote(
            gas_limit=estimated_gas,
            gas_price_wei=gas_price_wei,
            native_usd=native_usd.usd,
            gas_usd=gas_usd,
        )
        return GasEvidence(
            quote=quote,
            chain_id=first_head.chain_id,
            observed_block=first_head.block_number,
            price_observation=native_usd,
        )

    def _estimate_gas(self, transaction: dict[str, Any]) -> int:
        result = self._transport.request("eth_estimateGas", [transaction])
        if not isinstance(result, str) or not result.startswith("0x"):
            raise RpcError("eth_estimateGas returned malformed result")
        try:
            estimated = int(result, 16)
        except ValueError as exc:
            raise RpcError("eth_estimateGas returned invalid hexadecimal result") from exc
        if estimated <= 0:
            raise RpcError("eth_estimateGas returned a non-positive gas estimate")
        return estimated

    def _gas_price(self) -> int:
        result = self._transport.request("eth_gasPrice", [])
        if not isinstance(result, str) or not result.startswith("0x"):
            raise RpcError("eth_gasPrice returned malformed result")
        try:
            gas_price = int(result, 16)
        except ValueError as exc:
            raise RpcError("eth_gasPrice returned invalid hexadecimal result") from exc
        if gas_price <= 0:
            raise RpcError("eth_gasPrice returned a non-positive value")
        return gas_price
