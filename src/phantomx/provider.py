from __future__ import annotations

from dataclasses import dataclass
import re

from .chain_rpc import ChainRpcAdapter, RpcError

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
ZERO_ADDRESS = "0x" + "0" * 40


@dataclass(frozen=True)
class ProviderIdentity:
    name: str
    chain_id: int
    contract_address: str
    observed_block: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("provider name must be non-empty")
        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")
        if not ADDRESS_RE.fullmatch(self.contract_address):
            raise ValueError("provider contract address must be a valid EVM address")
        if self.contract_address.lower() == ZERO_ADDRESS.lower():
            raise ValueError("provider contract address must not be zero address")
        if self.observed_block < 0:
            raise ValueError("observed_block must be non-negative")


@dataclass(frozen=True)
class ProviderAuthenticityEvidence:
    identity: ProviderIdentity
    head_block: int
    code_present: bool


class ProviderAuthenticityValidator:
    """Read-only provider authenticity boundary for Gate 3.

    Provider identity is explicit and deployment evidence is checked at the
    exact observed block. No provider address, chain, or trust decision is
    inferred or substituted.
    """

    def __init__(self, rpc: ChainRpcAdapter) -> None:
        self._rpc = rpc

    def validate(self, identity: ProviderIdentity) -> ProviderAuthenticityEvidence:
        head = self._rpc.head()
        if head.chain_id != identity.chain_id:
            raise RpcError("provider chain id does not match runtime chain")
        if head.block_number != identity.observed_block:
            raise RpcError("provider evidence is not anchored to current head")

        code = self._rpc.code_at(
            identity.contract_address,
            block_tag=hex(identity.observed_block),
        )
        if not code:
            raise RpcError("provider contract has no deployed code at observation block")

        ending_head = self._rpc.head()
        if ending_head.chain_id != head.chain_id:
            raise RpcError("chain id changed during provider validation")
        if ending_head.block_number != head.block_number:
            raise RpcError("provider head advanced during authenticity validation")

        return ProviderAuthenticityEvidence(
            identity=identity,
            head_block=head.block_number,
            code_present=True,
        )
