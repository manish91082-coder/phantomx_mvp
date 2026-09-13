from __future__ import annotations

from dataclasses import dataclass

from .provider import ADDRESS_RE, ZERO_ADDRESS


@dataclass(frozen=True)
class FlashLoanExecutionContext:
    """Exact flash-loan callback context authorized for one execution."""

    provider: str
    borrower: str
    asset: str
    amount: int
    execution_id: str
    observed_block: int

    def __post_init__(self) -> None:
        for field_name, address in (("provider", self.provider), ("borrower", self.borrower), ("asset", self.asset)):
            if not ADDRESS_RE.fullmatch(address):
                raise ValueError(f"{field_name} must be a valid EVM address")
            if address.lower() == ZERO_ADDRESS.lower():
                raise ValueError(f"{field_name} must not be zero address")
        if self.amount <= 0:
            raise ValueError("amount must be positive")
        if not self.execution_id.strip():
            raise ValueError("execution_id must be non-empty")
        if self.observed_block < 0:
            raise ValueError("observed_block must be non-negative")


@dataclass(frozen=True)
class CallbackAuthorizationEvidence:
    execution_id: str
    sender: str
    authorized_provider: str
    observed_block: int


class CallbackAuthorizationError(ValueError):
    """Raised when a callback cannot be proven to belong to the active execution."""


class CallbackAuthorizer:
    """Deterministic fail-closed callback sender/context boundary.

    This is an authorization model only. It does not sign, broadcast, execute
    callbacks, or infer provider identity. A context is single-use: successful
    authorization consumes the execution id and prevents replay.
    """

    def __init__(self) -> None:
        self._active: FlashLoanExecutionContext | None = None
        self._consumed_execution_ids: set[str] = set()

    def arm(self, context: FlashLoanExecutionContext) -> None:
        if context.execution_id in self._consumed_execution_ids:
            raise CallbackAuthorizationError("execution context has already been consumed")
        if self._active is not None:
            raise CallbackAuthorizationError("another execution context is already active")
        self._active = context

    def authorize(
        self,
        *,
        sender: str,
        execution_id: str,
        observed_block: int,
        borrower: str,
        asset: str,
        amount: int,
    ) -> CallbackAuthorizationEvidence:
        context = self._active
        if context is None:
            raise CallbackAuthorizationError("no active flash-loan execution context")
        if not ADDRESS_RE.fullmatch(sender) or sender.lower() == ZERO_ADDRESS.lower():
            raise CallbackAuthorizationError("callback sender is invalid")
        if execution_id != context.execution_id:
            raise CallbackAuthorizationError("callback execution id does not match active context")
        if sender.lower() != context.provider.lower():
            raise CallbackAuthorizationError("callback sender is not the authenticated provider")
        if observed_block != context.observed_block:
            raise CallbackAuthorizationError("callback observation block is stale or mismatched")
        if borrower.lower() != context.borrower.lower():
            raise CallbackAuthorizationError("callback borrower does not match active context")
        if asset.lower() != context.asset.lower():
            raise CallbackAuthorizationError("callback asset does not match active context")
        if amount != context.amount:
            raise CallbackAuthorizationError("callback amount does not match active context")

        self._active = None
        self._consumed_execution_ids.add(context.execution_id)
        return CallbackAuthorizationEvidence(
            execution_id=context.execution_id,
            sender=sender,
            authorized_provider=context.provider,
            observed_block=context.observed_block,
        )

    def clear(self) -> None:
        """Explicitly invalidate an unconsumed active context."""
        self._active = None
