from decimal import Decimal

import pytest

from phantomx.chain_rpc import RpcError
from phantomx.runtime_evidence import PolygonGasEvidenceAdapter, UsdPriceObservation


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


def test_polygon_gas_quote_uses_runtime_rpc_and_explicit_usd_observation():
    transport = FakeTransport(
        [
            "0x89",          # eth_chainId = 137
            "0x100",         # eth_blockNumber
            "0x5208",        # eth_estimateGas = 21000
            "0x3b9aca00",    # eth_gasPrice = 1 gwei
            "0x89",          # stable eth_chainId
            "0x100",         # stable eth_blockNumber
        ]
    )
    adapter = PolygonGasEvidenceAdapter(transport)
    observation = UsdPriceObservation(
        usd=Decimal("0.50"), source="test-native-usd", observed_block=0x100
    )

    evidence = adapter.quote({"to": "0x" + "11" * 20}, observation)

    assert evidence.chain_id == 137
    assert evidence.observed_block == 0x100
    assert evidence.quote.gas_limit == 21000
    assert evidence.quote.gas_price_wei == 1_000_000_000
    assert evidence.quote.expected_wei == 21_000_000_000_000
    assert evidence.quote.gas_usd == Decimal("0.0000105")
    assert [method for method, _ in transport.calls] == [
        "eth_chainId",
        "eth_blockNumber",
        "eth_estimateGas",
        "eth_gasPrice",
        "eth_chainId",
        "eth_blockNumber",
    ]


def test_polygon_gas_quote_rejects_wrong_chain():
    transport = FakeTransport(["0x1", "0x100"])
    adapter = PolygonGasEvidenceAdapter(transport)
    observation = UsdPriceObservation(Decimal("1"), "test", 0x100)

    with pytest.raises(RpcError, match="unexpected chain id"):
        adapter.quote({"to": "0x" + "11" * 20}, observation)


def test_polygon_gas_quote_rejects_moving_head():
    transport = FakeTransport(
        [
            "0x89",
            "0x100",
            "0x5208",
            "0x3b9aca00",
            "0x89",
            "0x101",
        ]
    )
    adapter = PolygonGasEvidenceAdapter(transport)
    observation = UsdPriceObservation(Decimal("1"), "test", 0x100)

    with pytest.raises(RpcError, match="head advanced"):
        adapter.quote({"to": "0x" + "11" * 20}, observation)


def test_usd_observation_must_be_explicit_and_positive():
    with pytest.raises(ValueError, match="source must be non-empty"):
        UsdPriceObservation(Decimal("1"), "   ", 1)
    with pytest.raises(ValueError, match="finite and positive"):
        UsdPriceObservation(Decimal("0"), "test", 1)
