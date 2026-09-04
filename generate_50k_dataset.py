import json
import random
import sys

sys.stdout.reconfigure(encoding='utf-8')

def generate_dataset(num_samples=50000, output_file="training_dataset_50k.jsonl"):
    """
    Generates a massive, diverse dataset of 50,000 simulated MEV scenarios.
    This simulates the real conditions of the Polygon blockchain for training our AI.
    """
    print(f"🧬 [Data Gen] Generating {num_samples} Real-world MEV Scenarios...")
    
    with open(output_file, 'w') as f:
        for i in range(num_samples):
            # Simulate diverse market conditions
            base_price = random.uniform(10.0, 5000.0) # E.g., LINK at $15, ETH at $2500
            
            # Spread: from exactly 0 (no arb) to 5% (huge arb)
            spread_pct = random.uniform(-0.01, 0.05) 
            
            # Competitors' Bribe (Gas game theory)
            competitor_bribe_gwei = random.uniform(0.0, 150.0) # Sometimes no competitors, sometimes intense gas wars
            
            # Network state
            base_gas_fee_gwei = random.uniform(30.0, 600.0)
            
            # Liquidity Depth
            qs_reserves = random.uniform(5000, 10000000) # Quickswap USD reserves
            
            data_point = {
                "id": i,
                "qs_price": base_price,
                "uv3_price": base_price * (1 + spread_pct),
                "qs_usdc_reserves": qs_reserves,
                "base_gas_fee_gwei": base_gas_fee_gwei,
                "competitor_bribe_gwei": competitor_bribe_gwei
            }
            
            f.write(json.dumps(data_point) + '\n')
            
            if (i+1) % 10000 == 0:
                print(f"⏳ Generated {i+1}/{num_samples} scenarios...")
                
    print(f"✅ [Data Gen] Complete. Dataset saved to {output_file}")

if __name__ == "__main__":
    generate_dataset()
