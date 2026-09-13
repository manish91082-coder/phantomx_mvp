import pytest

from phantomx.callback import (
    CallbackAuthorizationError,
    CallbackAuthorizer,
    FlashLoanExecutionContext,
)

PROVIDER = "0x" + "11" * 20
BORROWER = "0x" + "22" * 20
ASSET = "0x" + "33" * 20
ATTACKER = "0x" + "44" * 20


def context() -> FlashLoanExecutionContext:
    return FlashLoanExecutionContext(
        provider=PROVIDER,
        borrower=BORROWER,
        asset=ASSET,
        amount=1_000_000,
        execution_id="exec-001",
        observed_block=500,
    )


def authorize_valid(authorizer: CallbackAuthorizer) -> None:
    authorizer.authorize(
        sender=PROVIDER,
        execution_id="exec-001",
        observed_block=500,
        borrower=BORROWER,
        asset=ASSET,
        amount=1_000_000,
    )


def test_valid_callback_is_authorized_and_consumes_context():
    authorizer = CallbackAuthorizer()
    authorizer.arm(context())
    evidence = authorizer.authorize(
        sender=PROVIDER,
        execution_id="exec-001",
        observed_block=500,
        borrower=BORROWER,
        asset=ASSET,
        amount=1_000_000,
    )
    assert evidence.execution_id == "exec-001"
    assert evidence.authorized_provider == PROVIDER

    with pytest.raises(CallbackAuthorizationError, match="no active"):
        authorize_valid(authorizer)


def test_unauthorized_sender_is_rejected():
    authorizer = CallbackAuthorizer()
    authorizer.arm(context())
    with pytest.raises(CallbackAuthorizationError, match="not the authenticated provider"):
        authorizer.authorize(
            sender=ATTACKER,
            execution_id="exec-001",
            observed_block=500,
            borrower=BORROWER,
            asset=ASSET,
            amount=1_000_000,
        )


def test_stale_block_is_rejected():
    authorizer = CallbackAuthorizer()
    authorizer.arm(context())
    with pytest.raises(CallbackAuthorizationError, match="stale or mismatched"):
        authorizer.authorize(
            sender=PROVIDER,
            execution_id="exec-001",
            observed_block=501,
            borrower=BORROWER,
            asset=ASSET,
            amount=1_000_000,
        )


def test_context_mismatch_is_rejected():
    cases = {
        "execution id": {"execution_id": "exec-002"},
        "borrower": {"borrower": ATTACKER},
        "asset": {"asset": ATTACKER},
        "amount": {"amount": 1_000_001},
    }
    for label, override in cases.items():
        authorizer = CallbackAuthorizer()
        authorizer.arm(context())
        kwargs = dict(
            sender=PROVIDER,
            execution_id="exec-001",
            observed_block=500,
            borrower=BORROWER,
            asset=ASSET,
            amount=1_000_000,
        )
        kwargs.update(override)
        with pytest.raises(CallbackAuthorizationError):
            authorizer.authorize(**kwargs)


def test_replay_and_rearm_after_success_are_rejected():
    authorizer = CallbackAuthorizer()
    authorizer.arm(context())
    authorize_valid(authorizer)
    with pytest.raises(CallbackAuthorizationError, match="already been consumed"):
        authorizer.arm(context())


def test_second_active_context_cannot_overwrite_first():
    authorizer = CallbackAuthorizer()
    authorizer.arm(context())
    second = FlashLoanExecutionContext(
        provider=PROVIDER,
        borrower=BORROWER,
        asset=ASSET,
        amount=2_000_000,
        execution_id="exec-002",
        observed_block=500,
    )
    with pytest.raises(CallbackAuthorizationError, match="already active"):
        authorizer.arm(second)


def test_invalid_context_values_fail_closed():
    with pytest.raises(ValueError):
        FlashLoanExecutionContext(PROVIDER, BORROWER, ASSET, 0, "exec", 500)
    with pytest.raises(ValueError):
        FlashLoanExecutionContext(PROVIDER, BORROWER, ASSET, 1, "", 500)
    with pytest.raises(ValueError):
        FlashLoanExecutionContext(PROVIDER, BORROWER, ASSET, 1, "exec", -1)
    with pytest.raises(ValueError):
        FlashLoanExecutionContext("0x1234", BORROWER, ASSET, 1, "exec", 500)
