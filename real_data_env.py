import gym
from gym import spaces
import numpy as np
import json
import math

class RealDataMossadEnv(gym.Env):
    """
    Mossad-Level Stress Test Environment for PhantomX AGI.
    Uses 100% REAL historical blockchain data (prices, gas, volatility).
    Penalties are extremely harsh to train for survivability in the Dark Forest.
    """
    def __init__(self, dataset_path="real_training_data_50k.jsonl"):
        super(RealDataMossadEnv, self).__init__()
        
        # Load dataset
        self.data = []
        with open(dataset_path, 'r') as f:
            for line in f:
                self.data.append(json.loads(line))
                
        self.current_step = 0
        self.max_steps = len(self.data)
        
        # Action space: [loan_pct, bribe_multiplier]
        self.action_space = spaces.Box(low=np.array([0.0, 0.0]), high=np.array([1.0, 3.0]), dtype=np.float32)
        
        # Observation space: [Spread, Reserves, Base Gas, Competitor Bribe, Real Price Volatility]
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32)

    def reset(self):
        self.current_step = 0
        return self._get_obs()

    def _get_obs(self):
        if self.current_step >= len(self.data):
            self.current_step = 0 
            
        row = self.data[self.current_step]
        spread = row["real_spread_pct"]
        reserves = row["qs_usdc_reserves"]
        base_gas = row["base_gas_fee_gwei"]
        comp_bribe = row["competitor_bribe_gwei"]
        real_price = row["real_price"]
        
        # We pass the real price as a volatility proxy to the AI
        return np.array([spread, reserves, base_gas, comp_bribe, real_price], dtype=np.float32)

    def step(self, action):
        row = self.data[self.current_step]
        spread = row["real_spread_pct"]
        reserves = row["qs_usdc_reserves"]
        base_gas = row["base_gas_fee_gwei"]
        comp_bribe = row["competitor_bribe_gwei"]
        
        loan_pct = action[0]
        bribe_mult = action[1]
        
        our_bribe_gwei = base_gas * bribe_mult
        
        reward = 0
        done = False
        info = {}
        
        # --- MOSSAD-LEVEL STRESS TEST LOGIC ---
        
        if spread <= 0.0005: # Spread must cover standard 0.05% DEX fee
            if loan_pct > 0:
                reward = -500 # Severe penalty for trading when unprofitable (Death by slippage)
            else:
                reward = 10  # Good survival instinct
        else:
            max_safe_loan = reserves * 0.005 # Stricter cap: max 0.5% of pool to avoid massive slippage
            loan_amt = max_safe_loan * loan_pct
            
            # Real Gross Profit
            gross_profit = loan_amt * spread
            
            # Real Gas Cost Calculation
            # In real Polygon, 1 Gwei = 1e-9 MATIC. A swap costs ~300,000 gas units.
            # MATIC price ~ $0.50. Let's assume a rough fixed multiplier for USD gas cost
            gas_cost_usd = (base_gas + our_bribe_gwei) * 300000 * 1e-9 * 0.50
            
            net_profit = gross_profit - gas_cost_usd
            
            # Did we win the Dark Forest gas war?
            if our_bribe_gwei >= comp_bribe:
                # We won the block!
                if net_profit > 0:
                    # Excellent trade. Reward is the exact dollar amount of net profit.
                    reward = net_profit * 10 
                else:
                    # We won the block but lost money on gas! (Pyrrhic victory)
                    reward = -1000 # Massive penalty. NEVER lose money.
            else:
                # We lost the gas war (Sandwiched or reverted)
                if loan_pct > 0.5:
                    # Tried to take a big loan but underpaid the bribe. Failed transaction cost.
                    reward = - (base_gas * 300000 * 1e-9 * 0.50) * 10
                else:
                    reward = -10
                
        self.current_step += 1
        if self.current_step >= self.max_steps:
            done = True
            
        return self._get_obs(), reward, done, info

if __name__ == "__main__":
    env = RealDataMossadEnv()
    obs = env.reset()
    print("🎯 Mossad-Level Real Environment Initialized.")
    print("Observation (Real Data):", obs)
