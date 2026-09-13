from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .market import MarketPair, PairMarketSnapshot
from .v2 import V2ReserveSnapshot, amount_out_v2


class Direction(str, Enum):
    BUY_ON_FIRST_SELL_ON_SECOND = "BUY_ON_FIRST_SELL_ON_SECOND"
    BUY_ON_SECOND_SELL_ON_FIRST = "BUY_ON_SECOND_SELL_ON_FIRST"


@dataclass(frozen=True)
class DirectArbQuote:
    pair: MarketPair
    buy_pool: V2ReserveSnapshot
    sell_pool: V2ReserveSnapshot
    input_amount: int
    intermediate_amount: int
    returned_amount: int
    gross_profit_units: int
    direction: Direction
    block_number: int

    @property
    def positive_gross_spread(self) -> bool:
        return self.gross_profit_units > 0


def _reserves_for_input(snapshot: V2ReserveSnapshot, input_token: str) -> tuple[int, int]:
    token = input_token.lower()
    if snapshot.pool.token0.lower() == token:
        return snapshot.reserve0, snapshot.reserve1
    if snapshot.pool.token1.lower() == token:
        return snapshot.reserve1, snapshot.reserve0
    raise ValueError("input token is not present in pool")


def quote_direct_two_pool(
    pair_snapshot: PairMarketSnapshot,
    buy_pool: V2ReserveSnapshot,
    sell_pool: V2ReserveSnapshot,
    input_amount: int,
    direction: Direction = Direction.BUY_ON_FIRST_SELL_ON_SECOND,
) -> DirectArbQuote:
    if input_amount <= 0:
        raise ValueError("input_amount must be positive")
    if buy_pool.pool.pair.lower() == sell_pool.pool.pair.lower():
        raise ValueError("buy and sell pools must be distinct")
    if buy_pool.block_number != sell_pool.block_number:
        raise ValueError("buy and sell pools must be from the same block")

    token_a = pair_snapshot.pair.token_a.address
    token_b = pair_snapshot.pair.token_b.address
    buy_in, buy_out = _reserves_for_input(buy_pool, token_a)
    intermediate = amount_out_v2(input_amount, buy_in, buy_out, buy_pool.pool.swap_fee_bps)
    sell_in, sell_out = _reserves_for_input(sell_pool, token_b)
    returned = amount_out_v2(intermediate, sell_in, sell_out, sell_pool.pool.swap_fee_bps)
    return DirectArbQuote(
        pair=pair_snapshot.pair,
        buy_pool=buy_pool,
        sell_pool=sell_pool,
        input_amount=input_amount,
        intermediate_amount=intermediate,
        returned_amount=returned,
        gross_profit_units=returned - input_amount,
        direction=direction,
        block_number=buy_pool.block_number,
    )


def enumerate_direct_quotes(pair_snapshot: PairMarketSnapshot, input_amount: int) -> tuple[DirectArbQuote, ...]:
    venues = pair_snapshot.venues
    quotes: list[DirectArbQuote] = []
    for index, first in enumerate(venues):
        for second in venues[index + 1 :]:
            quotes.append(
                quote_direct_two_pool(
                    pair_snapshot, first, second, input_amount,
                    Direction.BUY_ON_FIRST_SELL_ON_SECOND,
                )
            )
            quotes.append(
                quote_direct_two_pool(
                    pair_snapshot, second, first, input_amount,
                    Direction.BUY_ON_SECOND_SELL_ON_FIRST,
                )
            )
    return tuple(quotes)
