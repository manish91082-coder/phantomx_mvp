from __future__ import annotations

from dataclasses import dataclass

from .chain_rpc import ChainRpcAdapter, decode_address, decode_get_reserves, encode_get_pair
from .freshness import FreshnessGuard, Observation


GET_RESERVES_SELECTOR = "0x0902f1ac"
TOKEN0_SELECTOR = "0x0dfe1681"
TOKEN1_SELECTOR = "0xd21220a7"


@dataclass(frozen=True)
class Token:
    symbol: str
    address: str
    decimals: int


@dataclass(frozen=True)
class V2Venue:
    name: str
    factory: str
    swap_fee_bps: int = 30


@dataclass(frozen=True)
class V2Pool:
    venue: str
    pair: str
    token0: str
    token1: str


@dataclass(frozen=True)
class V2ReserveSnapshot:
    pool: V2Pool
    reserve0: int
    reserve1: int
    block_number: int


class V2PoolRegistry:
    def __init__(
        self,
        rpc: ChainRpcAdapter,
        venues: tuple[V2Venue, ...],
        freshness: FreshnessGuard,
    ) -> None:
        self._rpc = rpc
        self._venues = venues
        self._freshness = freshness

    def discover(self, token_a: Token, token_b: Token) -> list[V2Pool]:
        discovered: list[V2Pool] = []
        for venue in self._venues:
            raw_pair = self._rpc.eth_call(venue.factory, encode_get_pair(token_a.address, token_b.address))
            pair = decode_address(raw_pair)
            if int(pair, 16) == 0:
                continue
            code = self._rpc.code_at(pair)
            if not code:
                continue
            token0 = decode_address(self._rpc.eth_call(pair, TOKEN0_SELECTOR))
            token1 = decode_address(self._rpc.eth_call(pair, TOKEN1_SELECTOR))
            discovered.append(V2Pool(venue=venue.name, pair=pair, token0=token0, token1=token1))
        return discovered

    def reserves(self, pool: V2Pool) -> V2ReserveSnapshot:
        head = self._rpc.head()
        raw = self._rpc.eth_call(pool.pair, GET_RESERVES_SELECTOR, block_tag=hex(head.block_number))
        reserve0, reserve1, _ = decode_get_reserves(raw)
        snapshot = V2ReserveSnapshot(
            pool=pool,
            reserve0=reserve0,
            reserve1=reserve1,
            block_number=head.block_number,
        )
        self._freshness.assert_fresh(Observation(head.block_number, snapshot), head.block_number)
        return snapshot


def amount_out_v2(amount_in: int, reserve_in: int, reserve_out: int, fee_bps: int = 30) -> int:
    if amount_in <= 0 or reserve_in <= 0 or reserve_out <= 0:
        return 0
    if not 0 <= fee_bps < 10_000:
        raise ValueError("fee_bps must be in [0, 10000)")
    fee_denominator = 10_000
    amount_in_after_fee = amount_in * (fee_denominator - fee_bps)
    numerator = amount_in_after_fee * reserve_out
    denominator = reserve_in * fee_denominator + amount_in_after_fee
    return numerator // denominator
