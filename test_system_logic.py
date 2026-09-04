import pytest
from ai_brain import PhantomAIBrain
from risk_manager import RiskManager
from macro_ai import MacroStrategistAI
import random

# ==========================================
# TEST SUITE: AI Brain (Micro AI) Logic
# ==========================================
def test_ai_brain_initialization():
    brain = PhantomAIBrain()
    assert brain.total_decisions == 0
    assert brain.weights["profit_weight"] == 1.0

def test_ai_brain_calculate_optimal_loan():
    brain = PhantomAIBrain()
    # Scenario: Huge spread, lots of reserves
    qs_price, uv3_price, qs_usdc_reserves = 2500, 2550, 1000000
    loan = brain.calculate_optimal_loan(qs_price, uv3_price, qs_usdc_reserves)
    assert loan > 0
    assert loan <= qs_usdc_reserves * (brain.weights["slippage_tolerance"] / 2)
    
    # Scenario: No spread
    qs_price, uv3_price = 2500, 2500
    loan = brain.calculate_optimal_loan(qs_price, uv3_price, qs_usdc_reserves)
    assert loan == 0

def test_ai_brain_analyze_scenario_execute():
    brain = PhantomAIBrain()
    # Extremely profitable scenario
    decision, loan, profit, bribe = brain.analyze_scenario(2500, 2600, 1000000, 0.5)
    assert decision == "EXECUTE"
    assert loan > 0
    assert profit > 0.05
    assert bribe > 0

def test_ai_brain_analyze_scenario_ignore():
    brain = PhantomAIBrain()
    # Loss making scenario (High gas, no spread)
    decision, loan, profit, bribe = brain.analyze_scenario(2500, 2501, 1000000, 50.0)
    assert decision == "IGNORE"
    assert profit < 0
    assert bribe == 0

def test_ai_brain_bulk_scenarios():
    """Run 100+ simulated scenarios to ensure AI logic doesn't crash on edge cases"""
    brain = PhantomAIBrain()
    for _ in range(150):
        qs_price = random.uniform(100, 5000)
        uv3_price = qs_price * random.uniform(0.95, 1.05) # +/- 5% spread
        reserves = random.uniform(1000, 5000000)
        gas = random.uniform(0.1, 100.0)
        
        decision, loan, profit, bribe = brain.analyze_scenario(qs_price, uv3_price, reserves, gas)
        
        # Invariants
        assert decision in ["EXECUTE", "WAIT", "IGNORE"]
        if decision == "EXECUTE":
            assert profit >= 0.05
            
# ==========================================
# TEST SUITE: Risk Manager
# ==========================================
def test_risk_manager_high_gas(monkeypatch):
    mgr = RiskManager()
    
    # Mock web3 gas price to be very high
    class MockEth:
        @property
        def gas_price(self):
            return 600 * 10**9 # 600 Gwei
            
    class MockW3:
        eth = MockEth()
        def from_wei(self, val, unit):
            return val / 10**9
            
    mgr.w3 = MockW3()
    safe, status = mgr.check_network_health()
    
    assert safe is False
    assert status == "SLEEP_MODE: High Gas"

def test_risk_manager_safe_gas(monkeypatch):
    mgr = RiskManager()
    
    class MockEth:
        @property
        def gas_price(self):
            return 50 * 10**9 # 50 Gwei
            
    class MockW3:
        eth = MockEth()
        def from_wei(self, val, unit):
            return val / 10**9
            
    mgr.w3 = MockW3()
    safe, status = mgr.check_network_health()
    
    assert safe is True
    assert status == "SAFE"

# ==========================================
# TEST SUITE: Macro AI
# ==========================================
def test_macro_ai_sleep_mode():
    macro = MacroStrategistAI()
    strategy, targets = macro.determine_strategy("SLEEP_MODE: High Gas", {"LINK": "0x..."})
    assert strategy == "SLEEP_MODE"
    assert len(targets) == 0

def test_macro_ai_no_targets():
    macro = MacroStrategistAI()
    strategy, targets = macro.determine_strategy("SAFE", {})
    assert strategy == "WAIT"
    assert len(targets) == 0

def test_macro_ai_execute():
    macro = MacroStrategistAI()
    strategy, targets = macro.determine_strategy("SAFE", {"LINK": "0x123", "UNI": "0x456"})
    assert strategy == "SPATIAL_ARBITRAGE"
    assert len(targets) == 2
