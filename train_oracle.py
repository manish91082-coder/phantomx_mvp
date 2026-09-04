import json
import numpy as np
import sys
import os
import random

from adversarial_env import AdversarialMossadEnv

sys.stdout.reconfigure(encoding='utf-8')

class OracleTrainer:
    """
    Trains the Predictive AGI Oracle on the 1-Year Adversarial Environment.
    Implements cross-validation to prevent over-fitting.
    """
    def __init__(self, generations=100):
        self.env = AdversarialMossadEnv("sanitized_1yr_data.jsonl")
        self.generations = generations
        
        # We split the data manually for evaluation
        total_len = len(self.env.data)
        self.train_size = int(total_len * 0.8) # 80% train, 20% validation
        
        # Initial AI Weights (6 dimensions including Latency/JIT hint)
        self.weights_loan = np.random.randn(6) * 0.1
        self.weights_bribe = np.random.randn(6) * 0.1
        self.best_weights_loan = self.weights_loan.copy()
        self.best_weights_bribe = self.weights_bribe.copy()
        
        self.best_reward = -float('inf')
        self.log_file = "oracle_training_log.jsonl"
        open(self.log_file, 'w').close()

    def get_action(self, obs, weights_loan, weights_bribe):
        raw_loan = np.dot(obs, weights_loan)
        loan_pct = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        
        raw_bribe = np.dot(obs, weights_bribe)
        bribe_mult = min(max(raw_bribe, 0.0), 3.0)
        
        return [loan_pct, bribe_mult]
        
    def evaluate(self, weights_loan, weights_bribe, train_mode=True):
        total_reward = 0
        self.env.reset()
        
        start_idx = 0 if train_mode else self.train_size
        end_idx = self.train_size if train_mode else len(self.env.data)
        
        # Simulate over 1000 random samples in the set for speed
        samples = random.sample(range(start_idx, end_idx), min(1000, end_idx - start_idx))
        
        for idx in samples:
            self.env.current_step = idx
            obs = self.env._get_obs()
            
            # Simulated Dropout to prevent over-fitting (Randomly zero out one feature)
            if train_mode and random.random() < 0.1:
                drop_idx = random.randint(0, 5)
                obs[drop_idx] = 0.0
                
            action = self.get_action(obs, weights_loan, weights_bribe)
            _, reward, _, _ = self.env.step(action)
            total_reward += reward
            
        return total_reward

    def train(self):
        print("🛡️ [Oracle Training] Starting Final Boss Training on 1-Year Adversarial Data...")
        
        for gen in range(self.generations):
            noise_loan = np.random.normal(0, 0.2, 6)
            noise_bribe = np.random.normal(0, 0.2, 6)
            
            test_weights_loan = self.best_weights_loan + noise_loan if gen > 0 else self.weights_loan
            test_weights_bribe = self.best_weights_bribe + noise_bribe if gen > 0 else self.weights_bribe
            
            train_reward = self.evaluate(test_weights_loan, test_weights_bribe, train_mode=True)
            
            if train_reward > self.best_reward:
                # Cross-validate to ensure it didn't just over-fit the training set
                val_reward = self.evaluate(test_weights_loan, test_weights_bribe, train_mode=False)
                
                if val_reward > 0: # Only accept if it survives unseen data
                    self.best_reward = train_reward
                    self.best_weights_loan = test_weights_loan
                    self.best_weights_bribe = test_weights_bribe
                    
                    log_data = {
                        "generation": gen,
                        "train_reward": float(train_reward),
                        "val_reward": float(val_reward)
                    }
                    with open(self.log_file, 'a') as f:
                        f.write(json.dumps(log_data) + '\n')
                    
                    print(f"🏆 Gen {gen}: New Best! Train Reward = {train_reward:.2f} | Val Reward = {val_reward:.2f}")
            else:
                if gen % 10 == 0:
                    print(f"🔄 Gen {gen}: Train Reward {train_reward:.2f} (Best: {self.best_reward:.2f})")
                    
        print("✅ Final Oracle Training Complete.")
        self.export_weights()

    def export_weights(self):
        weights = {
            "loan_sizing_weights": self.best_weights_loan.tolist(),
            "dynamic_bribe_weights": self.best_weights_bribe.tolist()
        }
        with open("oracle_ai_weights.json", "w") as f:
            json.dump(weights, f, indent=4)
        print("💾 Oracle AI Weights exported to 'oracle_ai_weights.json'")

if __name__ == "__main__":
    trainer = OracleTrainer(generations=150)
    trainer.train()
