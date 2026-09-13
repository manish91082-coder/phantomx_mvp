from decimal import Decimal

import pytest

from phantomx.chain_rpc import RpcError
from phantomx.flash_fee import AaveV3PolygonFlashFeeAdapter


POOL = "0x" + "33" * 20


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, params):
        self.calls.append((method, params))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_aave_polygon_flash_fee_reads_live_premium():
    transport = FakeTransport(
        [
            "0x89",       # eth_chainId = 137
            "0x100",      # eth_blockNumber
            "0x60016001", # deployed code at the observation block
            "0x0000000000000000000000000000000000000000000000000000000000000032",  # 50 bps
            "0x89",       # stable chain id
            "0x100",      # stable head
        ]
    )
    adapter = AaveV3PolygonFlashFeeAdapter(transport, POOL)

    evidence = adapter.quote(Decimal("1000"))

    assert evidence.chain_id == 137
    assert evidence.observed_block == 0x100
    assert evidence.provider == "Aave V3"
    assert evidence.pool == POOL
    assert evidence.premium_bps == 50
    assert evidence.quote.flash_fee_usd == Decimal("5")
    assert [method for method, _ in transport.calls] == [
        "eth_chainId",
        "eth_blockNumber",
        "eth_getCode",
        "eth_call",
        "eth_chainId",
        "eth_blockNumber",
    ]


def test_aave_polygon_flash_fee_rejects_wrong_chain():
    transport = FakeTransport(["0x1", "0x100"])
    adapter = AaveV3PolygonFlashFeeAdapter(transport, POOL)

    with pytest.raises(RpcError, match="unexpected chain id"):
        adapter.quote(Decimal("1000"))


def test_aave_polygon_flash_fee_requires_pool_code():
    transport = FakeTransport(["0x89", "0x100", "0x"])
    adapter = AaveV3PolygonFlashFeeAdapter(transport, POOL)

    with pytest.raises(RpcError, match="no deployed code"):
        adapter.quote(Decimal("1000"))


def test_aave_polygon_flash_fee_rejects_moving_head():
    transport = FakeTransport(
        [
            "0x89",
            "0x100",
            "0x6001",
            "0x0000000000000000000000000000000000000000000000000000000000000032",
            "0x89",
            "0x101",
        ]
    )
    adapter = AaveV3PolygonFlashFeeAdapter(transport, POOL)

    with pytest.raises(RpcError, match="head advanced"):
        adapter.quote(Decimal("1000"))


def test_aave_polygon_flash_fee_rejects_non_positive_principal():
    transport = FakeTransport([])
    adapter = AaveV3PolygonFlashFeeAdapter(transport, POOL)

    with pytest.raises(ValueError, match="finite and positive"):
        adapter.quote(Decimal("0"))
