import json
import numpy as np
import time
import sys
import os

from live_mainnet_env import LiveMainnetEnv

sys.stdout.reconfigure(encoding='utf-8')

class LiveOracleTrainer:
    """
    Phase 16: Live Mainnet Deep Training.
    Trains the Oracle iteratively on real-time live blockchain data.
    """
    def __init__(self, target_iterations=50000, base_weights_file="oracle_ai_weights.json"):
        self.env = LiveMainnetEnv()
        self.target_iterations = target_iterations
        
        # Load previous weights to continue training (Transfer Learning)
        print("📥 Loading base weights from historical training...")
        if os.path.exists(base_weights_file):
            with open(base_weights_file, 'r') as f:
                weights = json.load(f)
                self.weights_loan = np.array(weights["loan_sizing_weights"])
                self.weights_bribe = np.array(weights["dynamic_bribe_weights"])
        else:
            print("⚠️ Base weights not found! Initializing randomly.")
            self.weights_loan = np.random.randn(6) * 0.1
            self.weights_bribe = np.random.randn(6) * 0.1
            
        self.learning_rate = 0.001
        self.log_file = "live_mainnet_training_log.jsonl"
        
        # Ensure log file exists but don't overwrite
        if not os.path.exists(self.log_file):
            open(self.log_file, 'w').close()

    def get_action(self, obs, explore_noise=0.1):
        raw_loan = np.dot(obs, self.weights_loan) + np.random.normal(0, explore_noise)
        loan_pct = 1 / (1 + np.exp(-raw_loan)) if raw_loan > -10 else 0
        
        raw_bribe = np.dot(obs, self.weights_bribe) + np.random.normal(0, explore_noise)
        bribe_mult = min(max(raw_bribe, 0.0), 3.0)
        
        return np.array([loan_pct, bribe_mult])

    def run_live_training(self):
        print(f"🌍 [Live Mainnet Training] Starting {self.target_iterations} Iterations...")
        
        total_reward = 0
        obs = self.env.reset()
        
        start_time = time.time()
        
        for i in range(self.target_iterations):
            action = self.get_action(obs, explore_noise=0.05)
            
            next_obs, reward, _, _ = self.env.step(action)
            total_reward += reward
            
            # Simple policy gradient update (Actor-Critic style approximation)
            # If reward is positive, reinforce the action taken
            # If reward is negative, decay the weights slightly
            update_factor = reward * self.learning_rate
            
            self.weights_loan += obs * update_factor * 0.01
            self.weights_bribe += obs * update_factor * 0.01
            
            # Normalize to prevent explosion
            self.weights_loan = np.clip(self.weights_loan, -10.0, 10.0)
            self.weights_bribe = np.clip(self.weights_bribe, -10.0, 10.0)
            
            obs = next_obs
            
            if i % 100 == 0 and i > 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                sys.stdout.write(f"\r🔥 Live Iteration: {i}/{self.target_iterations} | "
                                 f"Recent Reward: {reward:8.2f} | "
                                 f"Speed: {rate:5.1f} it/s")
                sys.stdout.flush()
                
                # Log periodically
                log_data = {
                    "iteration": i,
                    "timestamp": time.time(),
                    "cumulative_reward": float(total_reward),
                    "latest_reward": float(reward)
                }
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_data) + '\n')
                    
            # In a real environment we wait for the next block (2s)
            # Here we sleep briefly to respect API limits but simulate faster training
            time.sleep(0.01) 
            
        print("\n\n✅ Live Mainnet Training Complete.")
        
        # Save updated weights
        new_weights = {
            "loan_sizing_weights": self.weights_loan.tolist(),
            "dynamic_bribe_weights": self.weights_bribe.tolist()
        }
        with open("live_oracle_ai_weights.json", "w") as f:
            json.dump(new_weights, f, indent=4)
        print("💾 New Live Oracle AI Weights exported to 'live_oracle_ai_weights.json'")

if __name__ == "__main__":
    trainer = LiveOracleTrainer(target_iterations=50000)
    trainer.run_live_training()
