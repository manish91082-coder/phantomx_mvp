from __future__ import annotations

from dataclasses import dataclass

from .provider import ADDRESS_RE, ZERO_ADDRESS


@dataclass(frozen=True)
class AllowanceGrant:
    owner: str
    token: str
    spender: str
    execution_id: str
    amount_units: int

    def __post_init__(self) -> None:
        for field_name, address in (("owner", self.owner), ("token", self.token), ("spender", self.spender)):
            if not ADDRESS_RE.fullmatch(address):
                raise ValueError(f"{field_name} must be a valid EVM address")
            if address.lower() == ZERO_ADDRESS.lower():
                raise ValueError(f"{field_name} must not be zero address")
        if not self.execution_id.strip():
            raise ValueError("execution_id must be non-empty")
        if self.amount_units <= 0:
            raise ValueError("amount_units must be positive")


class AllowanceAuthorizationError(ValueError):
    """Raised when an allowance operation is outside the active execution grant."""


class AllowanceLifecycle:
    """Deterministic model of a bounded, single-execution allowance lifecycle.

    This model does not submit ERC-20 transactions. It defines the authorization
    boundary required before an executor may create or revoke an allowance.
    """

    def __init__(self) -> None:
        self._active: AllowanceGrant | None = None

    @property
    def active(self) -> AllowanceGrant | None:
        return self._active

    def arm(self, grant: AllowanceGrant) -> None:
        if self._active is not None:
            raise AllowanceAuthorizationError("another allowance grant is already active")
        self._active = grant

    def authorize_spend(self, *, owner: str, token: str, spender: str, execution_id: str, amount_units: int) -> None:
        grant = self._require_active()
        self._match(grant, owner, token, spender, execution_id)
        if amount_units <= 0 or amount_units > grant.amount_units:
            raise AllowanceAuthorizationError("allowance spend exceeds exact bounded grant")

    def authorize_revoke(self, *, owner: str, token: str, spender: str, execution_id: str) -> None:
        grant = self._require_active()
        self._match(grant, owner, token, spender, execution_id)
        self._active = None

    def clear(self) -> None:
        self._active = None

    def _require_active(self) -> AllowanceGrant:
        if self._active is None:
            raise AllowanceAuthorizationError("no active allowance grant")
        return self._active

    @staticmethod
    def _match(grant: AllowanceGrant, owner: str, token: str, spender: str, execution_id: str) -> None:
        if owner.lower() != grant.owner.lower():
            raise AllowanceAuthorizationError("allowance owner does not match active grant")
        if token.lower() != grant.token.lower():
            raise AllowanceAuthorizationError("allowance token does not match active grant")
        if spender.lower() != grant.spender.lower():
            raise AllowanceAuthorizationError("allowance spender does not match active grant")
        if execution_id != grant.execution_id:
            raise AllowanceAuthorizationError("allowance execution id does not match active grant")
