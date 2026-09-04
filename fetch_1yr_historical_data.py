import requests
import json
import time
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BINANCE_API = "https://api.binance.com/api/v3/klines"
# Using 1-hour candles for 1 year to make sequence learning manageable (8760 points) 
# OR 5-min candles (105,120 points). Let's use 5-minute candles to keep granularity 
# while making 1-year training realistic for an LSTM on a local machine without GPU memory blowout.

def fetch_1yr_data(symbol="MATICUSDT", interval="5m", output_file="historical_1yr_data.jsonl"):
    print(f"📡 [Phase 14] Fetching 1-Year Historical Market Data for {symbol} ({interval} intervals)...")
    
    # 1 year = 365 days = 8760 hours = 105,120 (5-minute periods)
    total_expected = 105120
    chunks = total_expected // 1000 + 1 
    
    end_time = int(time.time() * 1000)
    
    with open(output_file, 'w') as f:
        for chunk in range(chunks):
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": 1000,
                "endTime": end_time
            }
            
            try:
                response = requests.get(BINANCE_API, params=params)
                data = response.json()
                
                if type(data) == dict and "msg" in data:
                    print(f"API Error: {data['msg']}")
                    break
                    
                if len(data) == 0:
                    break
                    
                for kline in reversed(data): # Process backwards in time
                    timestamp = kline[0]
                    open_price = float(kline[1])
                    high_price = float(kline[2])
                    low_price = float(kline[3])
                    close_price = float(kline[4])
                    volume = float(kline[5])
                    
                    # Spread proxy based on volatility
                    real_spread = abs(high_price - low_price) / (low_price if low_price > 0 else 1)
                    
                    # Simulated 1-year Polygon Base Gas spikes (Baseline 30-50, spikes to 500+)
                    base_gas_fee_gwei = 30.0 + (volume / 50000.0) 
                    base_gas_fee_gwei = min(1500.0, base_gas_fee_gwei) # Cap at 1500
                    
                    # Random JIT Liquidity Drop simulation (1% chance a whale pulls liquidity)
                    jit_drop = True if int(timestamp) % 100 < 1 else False
                    reserves = 5000000 + (volume * 10)
                    if jit_drop:
                        reserves = reserves * 0.1 # Liquidity crashes 90%
                    
                    # JIT and Competitor stats
                    comp_bribe = (real_spread * 10000) + (10 if base_gas_fee_gwei > 100 else 0)
                    
                    data_point = {
                        "timestamp": timestamp,
                        "close_price": close_price,
                        "real_spread_pct": real_spread,
                        "qs_usdc_reserves": reserves,
                        "base_gas_fee_gwei": base_gas_fee_gwei,
                        "competitor_bribe_gwei": comp_bribe,
                        "jit_liquidity_trap": jit_drop
                    }
                    
                    # Writing out backwards, we'll reverse it during sanitization if chronological is needed
                    f.write(json.dumps(data_point) + '\n')
                
                end_time = data[0][0] - 1
                sys.stdout.write(f"\r✅ Fetched chunk {chunk+1}/{chunks} (Total: {(chunk+1)*1000} records)")
                sys.stdout.flush()
                time.sleep(0.1) # Respect Binance rate limits
                
            except Exception as e:
                print(f"\nError fetching data: {e}")
                break
                
    print(f"\n🎯 [Data Extraction Complete] Saved 1-Year historical scenarios to {output_file}")

if __name__ == "__main__":
    fetch_1yr_data(symbol="MATICUSDT", interval="5m")
