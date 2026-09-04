import sys
import os
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

class PhantomAIBrain:
    """
    PhantomX AGI Brain for Dynamic Arbitrage & MEV Decision Making.
    Powered by Deep Training Weights (Out-of-the-box Intelligence on REAL DATA).
    """
    def __init__(self, weights_path="real_trained_ai_weights.json"):
        self.weights_loan = np.array([1.0, 0.5, -0.1, 0.0, 0.0]) # Fallback
        self.weights_bribe = np.array([0.0, 0.0, 1.0, 1.1, 0.0]) # Fallback
        
        if os.path.exists(weights_path):
            with open(weights_path, 'r') as f:
                data = json.load(f)
                self.weights_loan = np.array(data.get("loan_sizing_weights", self.weights_loan))
                self.weights_bribe = np.array(data.get("dynamic_bribe_weights", self.weights_bribe))
                print(f"🧠 AGI Weights Loaded from {weights_path}")
        else:
            print("⚠️ Warning: No trained weights found. Using fallbacks.")
            
        self.total_decisions = 0
        self.correct_decisions = 0
        self.consecutive_correct = 0

    def get_action(self, obs):
        """
        Uses trained neural weights to predict optimal loan size and bribe.
        """
        # Loan sizing logic (Sigmoid)
        raw_loan = np.dot(obs, self.weights_loan)
        loan_pct = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        
        # Bribe multiplier logic (Clipped 0 to 2)
        raw_bribe = np.dot(obs, self.weights_bribe)
        bribe_mult = min(max(raw_bribe, 0.0), 2.0)
        
        return loan_pct, bribe_mult

    def analyze_scenario(self, qs_price, uv3_price, qs_usdc_reserves, base_gas_fee_gwei, competitor_bribe_gwei=0):
        """
        Analyzes a market scenario using the AGI trained model.
        Returns: ACTION, OPTIMAL_LOAN, EXPECTED_PROFIT, MEV_BRIBE
        """
        self.total_decisions += 1
        
        spread_raw = abs(qs_price - uv3_price)
        spread_pct = spread_raw / max(qs_price, 1)
        
        if spread_pct <= 0.0001:
            return "IGNORE", 0, 0, 0
            
        # Prepare observation array matching the training environment (5 dimensions)
        # Using qs_price as real_price proxy since it's the base price
        obs = np.array([spread_pct, qs_usdc_reserves, base_gas_fee_gwei, competitor_bribe_gwei, qs_price])
        
        # Get AI Predictions
        loan_pct, bribe_mult = self.get_action(obs)
        
        if loan_pct == 0:
            return "IGNORE", 0, 0, 0
            
        # Calculate real values
        max_safe_borrow = qs_usdc_reserves * 0.01 # Max 1% of pool
        optimal_loan = max_safe_borrow * loan_pct
        
        # Dynamic Miner Tip (Instead of hardcoded 90%)
        mev_bribe_gwei = base_gas_fee_gwei * bribe_mult
        # If competitor is known, ensure we beat them but don't overpay too much if AI suggests less
        # (Though the AI weights should inherently learn this based on training)
        
        # Calculate expected profitability
        gross_profit = optimal_loan * spread_pct
        gas_cost_usd = (base_gas_fee_gwei + mev_bribe_gwei) * 0.05
        
        net_profit_estimate = gross_profit - gas_cost_usd
        
        if net_profit_estimate > 0.05:
            return "EXECUTE", optimal_loan, net_profit_estimate, mev_bribe_gwei
        elif net_profit_estimate > -1:
            return "WAIT", optimal_loan, net_profit_estimate, mev_bribe_gwei
        else:
            return "IGNORE", optimal_loan, net_profit_estimate, mev_bribe_gwei

    def record_result(self, was_correct):
        if was_correct:
            self.correct_decisions += 1
            self.consecutive_correct += 1
        else:
            self.consecutive_correct = 0

if __name__ == "__main__":
    brain = PhantomAIBrain()
    print("🧠 PhantomX AGI Brain (Deep Trained) Initialized")
    # Test Scenario: Base gas 50, Competitor 0, Spread 1%, Reserves 100k
    decision, loan, expected, bribe = brain.analyze_scenario(2500, 2525, 100000, 50.0, 0)
    print(f"Test -> Decision: {decision} | Optimal Loan: ${loan:.2f} | Net Profit: ${expected:.2f} | Dynamic Bribe: {bribe:.2f} Gwei")
