import pytest

from phantomx.repayment import (
    RepaymentAuthorizationError,
    RepaymentRequirement,
    authorize_repayment,
)

PROVIDER = "0x" + "11" * 20
BORROWER = "0x" + "22" * 20
ASSET = "0x" + "33" * 20
ATTACKER = "0x" + "44" * 20


def requirement() -> RepaymentRequirement:
    return RepaymentRequirement(
        provider=PROVIDER,
        borrower=BORROWER,
        asset=ASSET,
        principal_units=1_000_000,
        fee_units=5_000,
        execution_id="exec-001",
    )


def test_required_repayment_is_exact_principal_plus_fee():
    assert requirement().required_units == 1_005_000


def test_exact_repayment_is_authorized():
    authorize_repayment(
        requirement(), payer=BORROWER, asset=ASSET, amount_units=1_005_000
    )


@pytest.mark.parametrize(
    "payer,asset,amount,match",
    [
        (ATTACKER, ASSET, 1_005_000, "payer"),
        (BORROWER, ATTACKER, 1_005_000, "asset"),
        (BORROWER, ASSET, 1_004_999, "amount"),
        (BORROWER, ASSET, 1_005_001, "amount"),
    ],
)
def test_under_over_or_mismatched_repayment_fails_closed(payer, asset, amount, match):
    with pytest.raises(RepaymentAuthorizationError, match=match):
        authorize_repayment(
            requirement(), payer=payer, asset=asset, amount_units=amount
        )


def test_zero_or_malformed_addresses_fail_closed():
    bad = "0x" + "0" * 40
    with pytest.raises(ValueError):
        RepaymentRequirement(bad, BORROWER, ASSET, 1, 0, "exec")
    with pytest.raises(ValueError):
        RepaymentRequirement(PROVIDER, BORROWER, bad, 1, 0, "exec")
    with pytest.raises(RepaymentAuthorizationError, match="payer"):
        authorize_repayment(requirement(), payer=bad, asset=ASSET, amount_units=1_005_000)
