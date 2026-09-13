from __future__ import annotations

from dataclasses import dataclass

from .provider import ADDRESS_RE, ZERO_ADDRESS


@dataclass(frozen=True)
class RepaymentRequirement:
    """Exact asset-unit repayment obligation for one flash-loan execution."""

    provider: str
    borrower: str
    asset: str
    principal_units: int
    fee_units: int
    execution_id: str

    def __post_init__(self) -> None:
        for field_name, address in (
            ("provider", self.provider),
            ("borrower", self.borrower),
            ("asset", self.asset),
        ):
            if not ADDRESS_RE.fullmatch(address):
                raise ValueError(f"{field_name} must be a valid EVM address")
            if address.lower() == ZERO_ADDRESS.lower():
                raise ValueError(f"{field_name} must not be zero address")
        if self.principal_units <= 0:
            raise ValueError("principal_units must be positive")
        if self.fee_units < 0:
            raise ValueError("fee_units must be non-negative")
        if not self.execution_id.strip():
            raise ValueError("execution_id must be non-empty")

    @property
    def required_units(self) -> int:
        return self.principal_units + self.fee_units


class RepaymentAuthorizationError(ValueError):
    """Raised when an observed repayment cannot satisfy the exact obligation."""


def authorize_repayment(
    requirement: RepaymentRequirement,
    *,
    payer: str,
    asset: str,
    amount_units: int,
) -> None:
    """Fail closed unless payer, asset, and exact repayment amount match."""

    if not ADDRESS_RE.fullmatch(payer) or payer.lower() == ZERO_ADDRESS.lower():
        raise RepaymentAuthorizationError("repayment payer is invalid")
    if payer.lower() != requirement.borrower.lower():
        raise RepaymentAuthorizationError("repayment payer does not match borrower")
    if asset.lower() != requirement.asset.lower():
        raise RepaymentAuthorizationError("repayment asset does not match borrowed asset")
    if amount_units != requirement.required_units:
        raise RepaymentAuthorizationError(
            "repayment amount does not exactly match principal plus flash fee"
        )
