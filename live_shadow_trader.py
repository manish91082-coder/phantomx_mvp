import json
import numpy as np
import time
import sys
import random

sys.stdout.reconfigure(encoding='utf-8')

class LiveShadowTrader:
    """
    Phase 15: Live Market Shadow Trading.
    Uses the trained Oracle AGI weights to simulate real-time trading against live Mempool conditions.
    """
    def __init__(self, weights_file="oracle_ai_weights.json"):
        print("🦇 [Shadow Trader] Initializing PhantomX Live Shadow Mode...")
        try:
            with open(weights_file, 'r') as f:
                weights = json.load(f)
                self.weights_loan = np.array(weights["loan_sizing_weights"])
                self.weights_bribe = np.array(weights["dynamic_bribe_weights"])
            print("✅ Oracle AGI Weights loaded successfully.")
        except Exception as e:
            print(f"Error loading weights: {e}")
            sys.exit(1)
            
        self.virtual_balance_usd = 1000.0 # Starting with $1000 Virtual Capital

    def fetch_live_mempool_state(self):
        """
        Simulates fetching live data from wss:// Polygon RPC.
        In production, this connects to Alchemy/Infura WebSockets.
        """
        # Mocking a live volatile market
        base_gas = random.uniform(30.0, 150.0)
        
        # 10% chance of a Honeypot / JIT trap appearing
        is_trap = random.random() < 0.1
        
        spread = 0.005 if is_trap else max(0.0, random.normalvariate(0.002, 0.003))
        reserves = 5000000.0
        comp_bribe = base_gas + random.uniform(0.0, 20.0)
        
        jit_flag = 1.0 if is_trap else 0.0
        
        return np.array([spread, reserves, base_gas, comp_bribe, 1.0, jit_flag])

    def get_action(self, obs):
        raw_loan = np.dot(obs, self.weights_loan)
        loan_pct = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        
        raw_bribe = np.dot(obs, self.weights_bribe)
        bribe_mult = min(max(raw_bribe, 0.0), 3.0)
        
        return loan_pct, bribe_mult

    def run_shadow_loop(self, iterations=10):
        print(f"🚀 [Shadow Mode Activated] Virtual Balance: ${self.virtual_balance_usd:.2f}")
        print("Monitoring Mempool...\n")
        
        for i in range(iterations):
            time.sleep(1) # Wait for next block
            
            obs = self.fetch_live_mempool_state()
            spread, reserves, base_gas, comp_bribe, _, is_trap = obs
            
            sys.stdout.write(f"Block {i+1} | Spread: {spread*100:.2f}% | Gas: {base_gas:.0f} | JIT Trap: {'YES' if is_trap else 'NO'} -> ")
            
            loan_pct, bribe_mult = self.get_action(obs)
            
            if loan_pct > 0.1:
                our_bribe = base_gas * bribe_mult
                loan_amt = (reserves * 0.005) * loan_pct
                
                print(f"⚡ ORACLE ACTION: FIRE! Loan: ${loan_amt:.2f}, Bribe: {our_bribe:.0f} Gwei")
                
                if is_trap:
                    print("   ❌ FATAL: Trapped in Honeypot! (-$50)")
                    self.virtual_balance_usd -= 50
                elif spread <= 0.001:
                    print("   ❌ SLIPPAGE: Not enough margin! (-$5)")
                    self.virtual_balance_usd -= 5
                elif our_bribe < comp_bribe:
                    print(f"   ⚠️ SANDWICHED! Outbid by {comp_bribe - our_bribe:.0f} Gwei. (-$2)")
                    self.virtual_balance_usd -= 2
                else:
                    gross = loan_amt * spread
                    gas_cost = (base_gas + our_bribe) * 300000 * 1e-9 * 0.5
                    net = gross - gas_cost
                    if net > 0:
                        print(f"   ✅ SUCCESS! Arb Captured: +${net:.2f}")
                        self.virtual_balance_usd += net
                    else:
                        print(f"   ⚠️ NEGATIVE PNL! Lost on Gas: ${net:.2f}")
                        self.virtual_balance_usd += net
            else:
                print("🛑 ORACLE ACTION: PASS (Too Risky)")
                
        print(f"\n🏁 Shadow Run Complete. Final Virtual Balance: ${self.virtual_balance_usd:.2f}")

if __name__ == "__main__":
    trader = LiveShadowTrader()
    trader.run_shadow_loop(iterations=20)
