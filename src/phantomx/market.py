from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .chain_rpc import ChainRpcAdapter
from .freshness import FreshnessGuard, Observation
from .v2 import Token, V2PoolRegistry, V2ReserveSnapshot


@dataclass(frozen=True)
class MarketPair:
    token_a: Token
    token_b: Token


@dataclass(frozen=True)
class PairMarketSnapshot:
    pair: MarketPair
    venues: tuple[V2ReserveSnapshot, ...]


@dataclass(frozen=True)
class MarketSnapshot:
    chain_id: int
    block_number: int
    pairs: tuple[PairMarketSnapshot, ...]


class ReadOnlyMarketReader:
    """Build a market snapshot without signing, sending, or mutating state."""

    def __init__(self, rpc: ChainRpcAdapter, registry: V2PoolRegistry, freshness: FreshnessGuard) -> None:
        self._rpc = rpc
        self._registry = registry
        self._freshness = freshness

    def snapshot(self, pairs: Iterable[MarketPair]) -> MarketSnapshot:
        head = self._rpc.head()
        if head.chain_id <= 0:
            raise ValueError("invalid chain id")

        results: list[PairMarketSnapshot] = []
        for pair in pairs:
            if pair.token_a.address.lower() == pair.token_b.address.lower():
                raise ValueError("market pair tokens must differ")
            pools = self._registry.discover(pair.token_a, pair.token_b)
            venue_snapshots = tuple(self._registry.reserves(pool) for pool in pools)
            for observation in venue_snapshots:
                self._freshness.assert_fresh(
                    Observation(observation.block_number, observation), head.block_number
                )
            results.append(PairMarketSnapshot(pair=pair, venues=venue_snapshots))

        return MarketSnapshot(chain_id=head.chain_id, block_number=head.block_number, pairs=tuple(results))
