import gym
from gym import spaces
import numpy as np
import random
import json
import math

class DynamicBribeEnv(gym.Env):
    """
    Custom Environment for training the Micro AI (Loan Sizing & Miner Tip/Bribe).
    Action Space: 
      [Loan multiplier (0.0 to 1.0 of max available),
       Bribe multiplier (0.0 to 2.0 of base gas fee)]
    Observation Space:
      [Spread %, Liquidity, Base Gas, Competitor Bribe]
    """
    def __init__(self, dataset_path="training_dataset_50k.jsonl"):
        super(DynamicBribeEnv, self).__init__()
        
        # Load dataset
        self.data = []
        with open(dataset_path, 'r') as f:
            for line in f:
                self.data.append(json.loads(line))
                
        self.current_step = 0
        self.max_steps = len(self.data)
        
        # Action space: [loan_pct, bribe_multiplier]
        # loan_pct: 0 to 1 (0% to 100% of max safe loan)
        # bribe_multiplier: 0 to 2 (0% to 200% of base gas added as tip)
        self.action_space = spaces.Box(low=np.array([0.0, 0.0]), high=np.array([1.0, 2.0]), dtype=np.float32)
        
        # Observation space: [Spread, Reserves, Base Gas, Competitor Bribe]
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32)

    def reset(self):
        self.current_step = 0
        return self._get_obs()

    def _get_obs(self):
        if self.current_step >= len(self.data):
            self.current_step = 0 # loop around if needed
            
        row = self.data[self.current_step]
        
        # Calculate spread
        qs_p = row["qs_price"]
        uv3_p = row["uv3_price"]
        spread = (uv3_p - qs_p) / qs_p
        
        reserves = row["qs_usdc_reserves"]
        base_gas = row["base_gas_fee_gwei"]
        comp_bribe = row["competitor_bribe_gwei"]
        
        return np.array([spread, reserves, base_gas, comp_bribe], dtype=np.float32)

    def step(self, action):
        row = self.data[self.current_step]
        qs_p = row["qs_price"]
        uv3_p = row["uv3_price"]
        reserves = row["qs_usdc_reserves"]
        base_gas = row["base_gas_fee_gwei"]
        comp_bribe = row["competitor_bribe_gwei"]
        
        loan_pct = action[0]
        bribe_mult = action[1]
        
        our_bribe_gwei = base_gas * bribe_mult
        
        # --- GAME THEORY LOGIC ---
        reward = 0
        done = False
        info = {}
        
        spread = (uv3_p - qs_p) / qs_p
        
        # If there's no spread, taking a loan is bad
        if spread <= 0:
            if loan_pct > 0:
                reward = -50 # Penalty for trading a losing pair
            else:
                reward = 10  # Reward for correctly ignoring
        else:
            # We have a spread. Calculate gross profit
            max_safe_loan = reserves * 0.01 # can borrow up to 1% without crushing pool
            loan_amt = max_safe_loan * loan_pct
            
            gross_profit = loan_amt * spread
            
            # Calculate Gas Cost (Simplified)
            gas_cost_usd = (base_gas + our_bribe_gwei) * 0.05 # Roughly $0.05 per gwei for the tx
            
            net_profit = gross_profit - gas_cost_usd
            
            # Did we win the block?
            if our_bribe_gwei > comp_bribe:
                # We won!
                if net_profit > 0:
                    reward = net_profit # We want to maximize this!
                else:
                    reward = -20 # Overpaid in bribe, lost money
            else:
                # We lost to competitor (Sandwiched or failed)
                # We still pay base gas for the failed tx
                reward = - (base_gas * 0.05) 
                
        self.current_step += 1
        if self.current_step >= self.max_steps:
            done = True
            
        return self._get_obs(), reward, done, info

if __name__ == "__main__":
    env = DynamicBribeEnv()
    obs = env.reset()
    print("Environment Initialized.")
    print("Initial Observation:", obs)
