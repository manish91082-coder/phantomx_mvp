from phantomx.flash_fee import AAVE_V3_FLASHLOAN_PREMIUM_TOTAL_SELECTOR


def test_aave_v3_flash_premium_selector_is_anchored():
    assert AAVE_V3_FLASHLOAN_PREMIUM_TOTAL_SELECTOR == "0x074b2e43"
