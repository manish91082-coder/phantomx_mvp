import sys
import random
import math

sys.stdout.reconfigure(encoding='utf-8')

class PhantomAIBrain:
    """
    PhantomX AI Brain for Dynamic Arbitrage Decision Making
    """
    def __init__(self):
        # AI Weights (can be adjusted during training via backpropagation/RL)
        self.weights = {
            "profit_weight": 1.0,
            "gas_penalty": 1.0,
            "slippage_tolerance": 0.005  # 0.5% base slippage
        }
        self.total_decisions = 0
        self.correct_decisions = 0
        self.consecutive_correct = 0

    def calculate_optimal_loan(self, qs_price, uv3_price, qs_usdc_reserves):
        """
        Dynamically calculates the optimal flash loan amount.
        Instead of a fixed $1000, we optimize the loan size so that the slippage
        doesn't eat the profit.
        """
        spread_raw = abs(qs_price - uv3_price)
        spread_pct = spread_raw / max(qs_price, 1)
        
        if spread_pct < 0.0001:
            return 0 # No spread, no loan
            
        # Approximation of optimal size: borrow up to a fraction of the pool's USDC reserves
        # proportional to the spread percentage, capped by max slippage tolerance.
        # This is a simplified proxy for the exact x*y=k calculus.
        max_safe_borrow = qs_usdc_reserves * (self.weights["slippage_tolerance"] / 2)
        
        # If the spread is huge, borrow more (up to safe max). If small, borrow less.
        optimal_loan = max_safe_borrow * (spread_pct * 100) # Scaling factor
        
        # Cap it between $10 (to cover minimal gas) and the max safe borrow
        optimal_loan = max(10, min(optimal_loan, max_safe_borrow))
        return optimal_loan

    def analyze_scenario(self, qs_price, uv3_price, qs_usdc_reserves, gas_fee_usdc):
        """
        Analyzes a single market scenario and makes a decision with dynamic loan size.
        Returns: ACTION, OPTIMAL_LOAN, EXPECTED_PROFIT, MEV_BRIBE
        ACTIONS: EXECUTE, WAIT, IGNORE
        """
        self.total_decisions += 1
        
        loan_amount_usdc = self.calculate_optimal_loan(qs_price, uv3_price, qs_usdc_reserves)
        if loan_amount_usdc == 0:
            return "IGNORE", 0, 0, 0
            
        spread_raw = abs(qs_price - uv3_price)
        spread_pct = spread_raw / max(qs_price, 1)
        
        # Calculate Gross Profit
        gross_profit = spread_pct * loan_amount_usdc
        
        # Dynamic Slippage (larger loan = more slippage)
        dynamic_slippage = loan_amount_usdc * (loan_amount_usdc / max(qs_usdc_reserves, 1))
        
        net_profit_estimate = (gross_profit * self.weights["profit_weight"]) - (gas_fee_usdc * self.weights["gas_penalty"]) - dynamic_slippage
        
        # -------------------------------------------------------------
        # MEV Dark Forest Bidding Logic
        # -------------------------------------------------------------
        # To win the gas war without public mempool sandwiching, 
        # we give 90% of our net profit directly to the block builder (Bribe)
        # and keep 10% as our guaranteed, risk-free profit.
        
        if net_profit_estimate > 0:
            mev_bribe = net_profit_estimate * 0.90
            final_guaranteed_profit = net_profit_estimate * 0.10
        else:
            mev_bribe = 0
            final_guaranteed_profit = net_profit_estimate

        # Decision Logic
        if final_guaranteed_profit > 0.05: # Require at least 5 cents clear net profit AFTER bribe
            return "EXECUTE", loan_amount_usdc, final_guaranteed_profit, mev_bribe
        elif final_guaranteed_profit > -1:
            return "WAIT", loan_amount_usdc, final_guaranteed_profit, mev_bribe
        else:
            return "IGNORE", loan_amount_usdc, final_guaranteed_profit, mev_bribe
            
    def update_weights(self, actual_profit, expected_profit):
        error = expected_profit - actual_profit
        if error > 0:
            self.weights["gas_penalty"] += 0.01
            self.weights["slippage_tolerance"] = max(0.001, self.weights["slippage_tolerance"] - 0.0001)
        else:
            self.weights["gas_penalty"] = max(0.5, self.weights["gas_penalty"] - 0.01)

    def record_result(self, was_correct):
        if was_correct:
            self.correct_decisions += 1
            self.consecutive_correct += 1
        else:
            self.consecutive_correct = 0

if __name__ == "__main__":
    brain = PhantomAIBrain()
    print("🧠 Dynamic AI Brain Initialized (Dark Forest Ready)")
    decision, loan, expected, bribe = brain.analyze_scenario(2500, 2525, 1000000, 0.5)
    print(f"Test -> Decision: {decision} | Optimal Loan: ${loan:.2f} | Guaranteed Net Profit: ${expected:.2f} | MEV Miner Bribe: ${bribe:.2f}")
