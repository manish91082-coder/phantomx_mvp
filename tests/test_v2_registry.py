from phantomx.chain_rpc import ChainRpcAdapter, RpcError
from phantomx.freshness import FreshnessGuard, FreshnessPolicy
from phantomx.v2 import Token, V2PoolRegistry, V2Venue


class DiscoveryRpc:
    def request(self, method, params):
        if method == "eth_chainId":
            return "0x89"
        if method == "eth_blockNumber":
            return "0x100"
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
        raise RpcError("unexpected request")


def test_v2_registry_discovers_nonzero_live_contract_code() -> None:
    rpc = ChainRpcAdapter(DiscoveryRpc())
    registry = V2PoolRegistry(
        rpc,
        (V2Venue("QuickSwap V2", "0x" + "33" * 20),),
        FreshnessGuard(FreshnessPolicy()),
    )
    pools = registry.discover(
        Token("A", "0x" + "44" * 20, 18),
        Token("B", "0x" + "55" * 20, 18),
    )
    assert len(pools) == 1
    assert pools[0].pair == "0x" + "ab" * 20
    assert pools[0].token0 == "0x" + "11" * 20
    assert pools[0].token1 == "0x" + "22" * 20
