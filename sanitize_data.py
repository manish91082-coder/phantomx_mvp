import json
import numpy as np
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def sanitize_and_prepare(input_file="historical_1yr_data.jsonl", output_file="sanitized_1yr_data.jsonl"):
    print(f"🧹 [Phase 14] Sanitizing 1-Year Historical Data: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    data = []
    with open(input_file, 'r') as f:
        for line in f:
            try:
                row = json.loads(line)
                data.append(row)
            except json.JSONDecodeError:
                continue

    print(f"Loaded {len(data)} raw records. Reversing to chronological order...")
    data.reverse() # The fetcher fetched backwards in time, reverse to chronological
    
    sanitized = []
    anomalies_removed = 0
    
    for row in data:
        # Check for NaN or extremely malformed values
        if any(v is None for v in row.values()):
            anomalies_removed += 1
            continue
            
        # Basic bounds checking
        if row["real_spread_pct"] < 0 or row["real_spread_pct"] > 5.0: # 500% spread is anomalous
            anomalies_removed += 1
            continue
            
        if row["base_gas_fee_gwei"] <= 0 or row["base_gas_fee_gwei"] > 5000:
            row["base_gas_fee_gwei"] = min(5000.0, max(1.0, row["base_gas_fee_gwei"]))
            
        sanitized.append(row)
        
    print(f"Sanitization complete. Removed {anomalies_removed} anomalous records.")
    
    # Save the sanitized dataset
    with open(output_file, 'w') as f:
        for row in sanitized:
            f.write(json.dumps(row) + '\n')
            
    print(f"✅ Saved {len(sanitized)} clean records to {output_file}")

if __name__ == "__main__":
    sanitize_and_prepare()
