from __future__ import annotations

from phantomx.chain_rpc import (
    ChainRpcAdapter,
    RpcError,
    decode_get_reserves,
    encode_get_pair,
)
from phantomx.freshness import FreshnessGuard, FreshnessPolicy, Observation, StaleDataError
from phantomx.v2 import amount_out_v2


class FakeRpc:
    def __init__(self) -> None:
        self.calls = []

    def request(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId":
            return "0x89"
        if method == "eth_blockNumber":
            return "0x64"
        if method == "eth_getCode":
            return "0x60016000"
        if method == "eth_call":
            data = params[0]["data"]
            if data.startswith("0xe6a43905"):
                return "0x" + "00" * 12 + "12" * 20
            if data == "0x0902f1ac":
                return "0x" + (1000).to_bytes(32, "big").hex() + (2000).to_bytes(32, "big").hex() + (100).to_bytes(32, "big").hex()
            if data == "0x0dfe1681":
                return "0x" + "00" * 12 + "34" * 20
            if data == "0xd21220a7":
                return "0x" + "00" * 12 + "56" * 20
        raise RpcError(f"unexpected fake RPC call: {method} {params}")


def test_chain_head_and_code_use_rpc() -> None:
    fake = FakeRpc()
    adapter = ChainRpcAdapter(fake)
    assert adapter.head().chain_id == 137
    assert adapter.head().block_number == 100
    assert adapter.code_at("0x" + "12" * 20)


def test_get_pair_encoding_has_expected_selector_and_two_args() -> None:
    data = encode_get_pair("0x" + "11" * 20, "0x" + "22" * 20)
    assert data.startswith("0xe6a43905")
    assert len(data) == 2 + 8 + 64 + 64


def test_reserve_decode_and_v2_quote_are_integer_deterministic() -> None:
    raw = (1000).to_bytes(32, "big") + (2000).to_bytes(32, "big") + (100).to_bytes(32, "big")
    assert decode_get_reserves(raw) == (1000, 2000, 100)
    assert amount_out_v2(100, 1000, 2000, 30) == 181


def test_freshness_guard_blocks_stale_observation() -> None:
    guard = FreshnessGuard(FreshnessPolicy(max_block_lag=2))
    guard.assert_fresh(Observation(100, "ok"), 102)
    try:
        guard.assert_fresh(Observation(100, "old"), 103)
    except StaleDataError:
        pass
    else:
        raise AssertionError("stale data was accepted")
