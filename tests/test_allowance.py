import pytest

from phantomx.allowance import AllowanceAuthorizationError, AllowanceGrant, AllowanceLifecycle

OWNER = "0x" + "11" * 20
TOKEN = "0x" + "22" * 20
SPENDER = "0x" + "33" * 20
ATTACKER = "0x" + "44" * 20


def grant():
    return AllowanceGrant(OWNER, TOKEN, SPENDER, "exec-001", 1_000_000)


def test_exact_bounded_spend_is_authorized():
    lifecycle = AllowanceLifecycle()
    lifecycle.arm(grant())
    lifecycle.authorize_spend(owner=OWNER, token=TOKEN, spender=SPENDER, execution_id="exec-001", amount_units=1_000_000)


def test_zero_or_oversized_spend_fails_closed():
    lifecycle = AllowanceLifecycle()
    lifecycle.arm(grant())
    for amount in (0, 1_000_001):
        with pytest.raises(AllowanceAuthorizationError, match="exceeds exact bounded grant"):
            lifecycle.authorize_spend(owner=OWNER, token=TOKEN, spender=SPENDER, execution_id="exec-001", amount_units=amount)


@pytest.mark.parametrize(
    "owner,token,spender,execution_id,match",
    [
        (ATTACKER, TOKEN, SPENDER, "exec-001", "owner"),
        (OWNER, ATTACKER, SPENDER, "exec-001", "token"),
        (OWNER, TOKEN, ATTACKER, "exec-001", "spender"),
        (OWNER, TOKEN, SPENDER, "exec-002", "execution id"),
    ],
)
def test_wrong_context_fails_closed(owner, token, spender, execution_id, match):
    lifecycle = AllowanceLifecycle()
    lifecycle.arm(grant())
    with pytest.raises(AllowanceAuthorizationError, match=match):
        lifecycle.authorize_spend(owner=owner, token=token, spender=spender, execution_id=execution_id, amount_units=1)


def test_second_grant_cannot_overwrite_active_grant():
    lifecycle = AllowanceLifecycle()
    lifecycle.arm(grant())
    second = AllowanceGrant(OWNER, TOKEN, SPENDER, "exec-002", 2)
    with pytest.raises(AllowanceAuthorizationError, match="already active"):
        lifecycle.arm(second)


def test_revoke_consumes_authorization_and_requires_same_context():
    lifecycle = AllowanceLifecycle()
    lifecycle.arm(grant())
    lifecycle.authorize_revoke(owner=OWNER, token=TOKEN, spender=SPENDER, execution_id="exec-001")
    with pytest.raises(AllowanceAuthorizationError, match="no active"):
        lifecycle.authorize_spend(owner=OWNER, token=TOKEN, spender=SPENDER, execution_id="exec-001", amount_units=1)


def test_revoke_wrong_context_fails_without_clearing_grant():
    lifecycle = AllowanceLifecycle()
    lifecycle.arm(grant())
    with pytest.raises(AllowanceAuthorizationError, match="spender"):
        lifecycle.authorize_revoke(owner=OWNER, token=TOKEN, spender=ATTACKER, execution_id="exec-001")
    assert lifecycle.active == grant()


def test_malformed_or_zero_addresses_fail_closed():
    bad = "0x" + "0" * 40
    with pytest.raises(ValueError):
        AllowanceGrant(bad, TOKEN, SPENDER, "exec", 1)
    with pytest.raises(ValueError):
        AllowanceGrant(OWNER, TOKEN, bad, "exec", 1)
    lifecycle = AllowanceLifecycle()
    lifecycle.arm(grant())
    with pytest.raises(AllowanceAuthorizationError, match="no active"):
        lifecycle.authorize_spend(owner=OWNER, token=TOKEN, spender=SPENDER, execution_id="exec-001", amount_units=1)
        

def test_clear_invalidates_active_grant():
    lifecycle = AllowanceLifecycle()
    lifecycle.arm(grant())
    lifecycle.clear()
    with pytest.raises(AllowanceAuthorizationError, match="no active"):
        lifecycle.authorize_revoke(owner=OWNER, token=TOKEN, spender=SPENDER, execution_id="exec-001")
