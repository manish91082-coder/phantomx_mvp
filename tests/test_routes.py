from phantomx.market import MarketPair, PairMarketSnapshot
from phantomx.routes import Direction, enumerate_direct_quotes, quote_direct_two_pool
from phantomx.v2 import Token, V2Pool, V2ReserveSnapshot


A = Token("A", "0x" + "11" * 20, 18)
B = Token("B", "0x" + "22" * 20, 18)


def pool(venue: str, address_byte: str, r0: int, r1: int) -> V2ReserveSnapshot:
    return V2ReserveSnapshot(
        V2Pool(venue, "0x" + address_byte * 20, A.address, B.address, 30),
        r0,
        r1,
        100,
    )


def test_direct_quote_rejects_mixed_blocks() -> None:
    first = pool("A", "a1", 1_000_000, 2_000_000)
    second = pool("B", "b2", 2_000_000, 1_000_000)
    mixed = V2ReserveSnapshot(second.pool, second.reserve0, second.reserve1, 101)
    pair = MarketPair(A, B)
    snapshot = PairMarketSnapshot(pair, (first, mixed))
    try:
        quote_direct_two_pool(snapshot, first, mixed, 10_000)
    except ValueError as exc:
        assert "same block" in str(exc)
    else:
        raise AssertionError("mixed-block quote was accepted")


def test_enumeration_builds_both_directions_without_profitability_authorization() -> None:
    first = pool("QuickSwap V2", "a1", 1_000_000, 2_000_000)
    second = pool("Uniswap V2", "b2", 2_100_000, 1_000_000)
    snapshot = PairMarketSnapshot(MarketPair(A, B), (first, second))
    quotes = enumerate_direct_quotes(snapshot, 10_000)
    assert len(quotes) == 2
    assert {q.direction for q in quotes} == {
        Direction.BUY_ON_FIRST_SELL_ON_SECOND,
        Direction.BUY_ON_SECOND_SELL_ON_FIRST,
    }
    assert all(q.block_number == 100 for q in quotes)
    assert all(q.input_amount == 10_000 for q in quotes)
