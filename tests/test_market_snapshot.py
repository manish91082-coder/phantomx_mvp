from phantomx.chain_rpc import ChainRpcAdapter, RpcError
from phantomx.freshness import FreshnessGuard, FreshnessPolicy
from phantomx.market import MarketPair, ReadOnlyMarketReader
from phantomx.v2 import Token, V2PoolRegistry, V2Venue


PAIR = "0x" + "ab" * 20


class SnapshotRpc:
    def __init__(self) -> None:
        self.methods = []

    def request(self, method, params):
        self.methods.append(method)
        if method == "eth_chainId":
            return "0x89"
        if method == "eth_blockNumber":
            return "0x200"
        if method == "eth_getCode":
            return "0x6001"
        if method == "eth_call":
            data = params[0]["data"]
            if data.startswith("0xe6a43905"):
                return "0x" + "00" * 12 + "ab" * 20
            if data == "0x0dfe1681":
                return "0x" + "00" * 12 + "11" * 20
            if data == "0xd21220a7":
                return "0x" + "00" * 12 + "22" * 20
            if data == "0x0902f1ac":
                return "0x" + (1000000).to_bytes(32, "big").hex() + (2000000).to_bytes(32, "big").hex() + (123).to_bytes(32, "big").hex()
        raise RpcError("unexpected call")


def test_read_only_market_snapshot_collects_head_pool_and_reserves() -> None:
    transport = SnapshotRpc()
    rpc = ChainRpcAdapter(transport)
    registry = V2PoolRegistry(
        rpc,
        (V2Venue("QuickSwap V2", "0x" + "33" * 20),),
        FreshnessGuard(FreshnessPolicy(max_block_lag=2)),
    )
    reader = ReadOnlyMarketReader(rpc, registry, FreshnessGuard(FreshnessPolicy()))
    snapshot = reader.snapshot(
        [MarketPair(Token("WETH", "0x" + "44" * 20, 18), Token("USDC", "0x" + "55" * 20, 6))]
    )
    assert snapshot.chain_id == 137
    assert snapshot.block_number == 512
    assert len(snapshot.pairs) == 1
    assert snapshot.pairs[0].venues[0].reserve0 == 1_000_000
    assert "eth_sendRawTransaction" not in transport.methods
    assert "eth_sendTransaction" not in transport.methods
