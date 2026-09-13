from phantomx.chain_rpc import ChainRpcAdapter, RpcError
from phantomx.provider import ProviderAuthenticityValidator, ProviderIdentity


class FakeTransport:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def request(self, method, params):
        self.calls.append((method, params))
        return next(self.responses)


PROVIDER = "0x" + "11" * 20


def test_provider_authenticity_requires_exact_chain_and_block_and_code():
    transport = FakeTransport([
        "0x89",
        "0x100",
        "0x60006000",
        "0x89",
        "0x100",
    ])
    validator = ProviderAuthenticityValidator(ChainRpcAdapter(transport))
    identity = ProviderIdentity("Aave V3", 137, PROVIDER, 256)

    evidence = validator.validate(identity)

    assert evidence.identity == identity
    assert evidence.code_present is True
    assert evidence.head_block == 256
    assert [call[0] for call in transport.calls] == [
        "eth_chainId", "eth_blockNumber", "eth_getCode", "eth_chainId", "eth_blockNumber"
    ]


def test_wrong_chain_is_rejected_before_code_lookup():
    transport = FakeTransport([
        "0x1",
        "0x100",
    ])
    validator = ProviderAuthenticityValidator(ChainRpcAdapter(transport))
    identity = ProviderIdentity("Aave V3", 137, PROVIDER, 256)

    try:
        validator.validate(identity)
    except RpcError as exc:
        assert "chain id" in str(exc)
    else:
        raise AssertionError("expected chain mismatch")

    assert [call[0] for call in transport.calls] == ["eth_chainId"]


def test_stale_observation_is_rejected():
    transport = FakeTransport([
        "0x89",
        "0x101",
    ])
    validator = ProviderAuthenticityValidator(ChainRpcAdapter(transport))
    identity = ProviderIdentity("Aave V3", 137, PROVIDER, 256)

    try:
        validator.validate(identity)
    except RpcError as exc:
        assert "anchored to current head" in str(exc)
    else:
        raise AssertionError("expected stale provider evidence rejection")


def test_missing_provider_code_is_rejected():
    transport = FakeTransport([
        "0x89",
        "0x100",
        "0x",
    ])
    validator = ProviderAuthenticityValidator(ChainRpcAdapter(transport))
    identity = ProviderIdentity("Aave V3", 137, PROVIDER, 256)

    try:
        validator.validate(identity)
    except RpcError as exc:
        assert "no deployed code" in str(exc)
    else:
        raise AssertionError("expected missing code rejection")


def test_identity_rejects_malformed_or_zero_provider_address():
    for address in ("0x1234", "0x" + "0" * 40):
        try:
            ProviderIdentity("Aave V3", 137, address, 256)
        except ValueError:
            pass
        else:
            raise AssertionError("expected provider address rejection")
