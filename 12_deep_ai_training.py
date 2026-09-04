import json
import random
import numpy as np
import os
import sys

from dynamic_bribe_env import DynamicBribeEnv

sys.stdout.reconfigure(encoding='utf-8')

class AITrainer:
    """
    Trains the Micro AI (Loan Sizing & Dynamic Bribe) using a 
    Reinforcement Learning approach (Evolutionary Strategy / Random Search)
    over 50,000 real/simulated transactions.
    """
    def __init__(self, generations=100, episodes_per_gen=500):
        self.env = DynamicBribeEnv("training_dataset_50k.jsonl")
        self.generations = generations
        self.episodes_per_gen = episodes_per_gen
        
        # Initial AI Weights [w_spread, w_reserves, w_gas, w_competitor]
        # We will mutate these to find the optimal policy.
        self.best_weights_loan = np.array([1.0, 0.5, -0.1, 0.0])
        self.best_weights_bribe = np.array([0.0, 0.0, 1.0, 1.1])
        self.best_reward = -float('inf')
        self.log_file = "training_log.jsonl"
        
        # Clear log file
        open(self.log_file, 'w').close()

    def get_action(self, obs, weights_loan, weights_bribe):
        # Neural Network (Linear combination with Sigmoid/ReLU)
        
        # Loan sizing logic
        raw_loan = np.dot(obs, weights_loan)
        # Sigmoid to keep between 0 and 1
        loan_pct = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        
        # Bribe multiplier logic
        raw_bribe = np.dot(obs, weights_bribe)
        # Bribe multiplier between 0 and 2
        bribe_mult = min(max(raw_bribe, 0.0), 2.0)
        
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
        print("🧠 Starting Deep AI Training (Out-of-the-box AGI)...")
        print(f"🎯 Target: Maximize Net MEV Profit over {self.generations * self.episodes_per_gen} steps.")
        
        for gen in range(self.generations):
            # Mutate weights
            noise_loan = np.random.normal(0, 0.2, 4)
            noise_bribe = np.random.normal(0, 0.2, 4)
            
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
                    
        print("✅ Training Complete.")
        self.export_weights()

    def export_weights(self):
        weights = {
            "loan_sizing_weights": self.best_weights_loan.tolist(),
            "dynamic_bribe_weights": self.best_weights_bribe.tolist()
        }
        with open("trained_ai_weights.json", "w") as f:
            json.dump(weights, f, indent=4)
        print("💾 Best AI Weights exported to 'trained_ai_weights.json'")

if __name__ == "__main__":
    trainer = AITrainer(generations=100, episodes_per_gen=500)
    trainer.train()
