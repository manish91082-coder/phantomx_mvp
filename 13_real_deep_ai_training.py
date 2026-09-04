import json
import random
import numpy as np
import os
import sys

from real_data_env import RealDataMossadEnv

sys.stdout.reconfigure(encoding='utf-8')

class MossadAITrainer:
    """
    Trains the AGI on 100% REAL historical blockchain data.
    Uses extreme stress testing logic.
    """
    def __init__(self, generations=100, episodes_per_gen=500):
        self.env = RealDataMossadEnv("real_training_data_50k.jsonl")
        self.generations = generations
        self.episodes_per_gen = episodes_per_gen
        
        # Initial AI Weights [w_spread, w_reserves, w_gas, w_competitor, w_realprice]
        self.best_weights_loan = np.array([1.0, 0.5, -0.1, 0.0, 0.0])
        self.best_weights_bribe = np.array([0.0, 0.0, 1.0, 1.1, 0.0])
        self.best_reward = -float('inf')
        self.log_file = "real_training_log.jsonl"
        
        # Clear log file
        open(self.log_file, 'w').close()

    def get_action(self, obs, weights_loan, weights_bribe):
        raw_loan = np.dot(obs, weights_loan)
        loan_pct = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        
        raw_bribe = np.dot(obs, weights_bribe)
        # Bribe multiplier between 0 and 3 (up to 3x base gas for extreme wars)
        bribe_mult = min(max(raw_bribe, 0.0), 3.0)
        
        return [loan_pct, bribe_mult]
        
    def evaluate(self, weights_loan, weights_bribe):
        total_reward = 0
        obs = self.env.reset()
        done = False
        
        for _ in range(self.episodes_per_gen):
            action = self.get_action(obs, weights_loan, weights_bribe)
            obs, reward, done, _ = self.env.step(action)
            total_reward += reward
            if done:
                break
                
        return total_reward

    def train(self):
        print("🛡️ Starting Mossad-Level Deep AI Training on REAL Data...")
        print(f"🎯 Target: Maximize Real Net Profit & Survivability over {self.generations * self.episodes_per_gen} steps.")
        
        for gen in range(self.generations):
            # Mutate weights
            noise_loan = np.random.normal(0, 0.3, 5)
            noise_bribe = np.random.normal(0, 0.3, 5)
            
            test_weights_loan = self.best_weights_loan + noise_loan
            test_weights_bribe = self.best_weights_bribe + noise_bribe
            
            reward = self.evaluate(test_weights_loan, test_weights_bribe)
            
            if reward > self.best_reward:
                self.best_reward = reward
                self.best_weights_loan = test_weights_loan
                self.best_weights_bribe = test_weights_bribe
                
                log_data = {
                    "generation": gen,
                    "reward": float(reward),
                    "best_weights_loan": test_weights_loan.tolist(),
                    "best_weights_bribe": test_weights_bribe.tolist()
                }
                
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_data) + '\n')
                
                print(f"🏆 Gen {gen}: New Best Reward = {reward:.2f}")
            else:
                if gen % 10 == 0:
                    print(f"🔄 Gen {gen}: Reward {reward:.2f} (Best: {self.best_reward:.2f})")
                    
        print("✅ Mossad Training Complete.")
        self.export_weights()

    def export_weights(self):
        weights = {
            "loan_sizing_weights": self.best_weights_loan.tolist(),
            "dynamic_bribe_weights": self.best_weights_bribe.tolist()
        }
        with open("real_trained_ai_weights.json", "w") as f:
            json.dump(weights, f, indent=4)
        print("💾 Real AI Weights exported to 'real_trained_ai_weights.json'")

if __name__ == "__main__":
    trainer = MossadAITrainer(generations=150, episodes_per_gen=1000)
    trainer.train()
