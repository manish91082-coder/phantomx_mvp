import gym
from gym import spaces
import numpy as np
import json
import math
import random

class AdversarialMossadEnv(gym.Env):
    """
    Phase 15: Extreme Adversarial Environment (The Final Boss).
    Includes:
    - JIT Liquidity Traps (-5000 penalty)
    - Sandwich Attacks (-1000 penalty)
    - RPC Latency Simulation (stale data)
    """
    def __init__(self, dataset_path="sanitized_1yr_data.jsonl"):
        super(AdversarialMossadEnv, self).__init__()
        
        self.data = []
        with open(dataset_path, 'r') as f:
            for line in f:
                self.data.append(json.loads(line))
                
        self.current_step = 0
        self.max_steps = len(self.data)
        
        # Action space: [loan_pct, bribe_multiplier]
        self.action_space = spaces.Box(low=np.array([0.0, 0.0]), high=np.array([1.0, 3.0]), dtype=np.float32)
        
        # Obs space: [Spread, Reserves, Base Gas, Comp Bribe, Real Price, JIT_Flag (stale)]
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32)

    def reset(self):
        self.current_step = 0
        return self._get_obs()

    def _get_obs(self):
        if self.current_step >= len(self.data):
            self.current_step = 0 
            
        row = self.data[self.current_step]
        
        # Latency Simulation: Agent sees data from 1 block ago sometimes
        if random.random() < 0.2 and self.current_step > 0:
            row = self.data[self.current_step - 1] # Stale data!
            
        spread = row["real_spread_pct"]
        reserves = row["qs_usdc_reserves"]
        base_gas = row["base_gas_fee_gwei"]
        comp_bribe = row["competitor_bribe_gwei"]
        real_price = row.get("close_price", 1.0)
        
        # Agent gets a hint about JIT, but it might be stale/noisy
        jit_flag = 1.0 if row.get("jit_liquidity_trap", False) else 0.0
        
        return np.array([spread, reserves, base_gas, comp_bribe, real_price, jit_flag], dtype=np.float32)

    def step(self, action):
        row = self.data[self.current_step]
        actual_spread = row["real_spread_pct"]
        actual_reserves = row["qs_usdc_reserves"]
        actual_gas = row["base_gas_fee_gwei"]
        actual_comp_bribe = row["competitor_bribe_gwei"]
        is_jit_trap = row.get("jit_liquidity_trap", False)
        
        loan_pct = action[0]
        bribe_mult = action[1]
        
        our_bribe = actual_gas * bribe_mult
        
        reward = 0
        done = False
        
        if loan_pct > 0:
            if is_jit_trap:
                # Traded into a Honeypot / JIT Liquidity rug pull
                reward = -5000 
            elif actual_spread <= 0.001:
                # Death by slippage/fees
                reward = -500
            else:
                max_safe_loan = actual_reserves * 0.005
                loan_amt = max_safe_loan * loan_pct
                
                gross_profit = loan_amt * actual_spread
                gas_cost_usd = (actual_gas + our_bribe) * 300000 * 1e-9 * 0.50
                net_profit = gross_profit - gas_cost_usd
                
                if our_bribe >= actual_comp_bribe:
                    if net_profit > 0:
                        reward = net_profit * 10
                    else:
                        reward = -1000 # Paid too much bribe, lost money
                else:
                    # Sandwiched / Outbid
                    reward = - (actual_gas * 300000 * 1e-9 * 0.50) * 10
        else:
            # Smartly avoided a trap
            if is_jit_trap or actual_spread <= 0.001:
                reward = 50
                
        self.current_step += 1
        if self.current_step >= self.max_steps:
            done = True
            
        return self._get_obs(), reward, done, {}

if __name__ == "__main__":
    env = AdversarialMossadEnv()
    obs = env.reset()
    print("🎯 Adversarial Mossad Env Initialized.")
    print("Obs:", obs)
