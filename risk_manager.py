import sys
from web3 import Web3

sys.stdout.reconfigure(encoding='utf-8')

class RiskManager:
    """
    Monitors market anomalies (e.g. extreme gas spikes, massive network congestion)
    to protect the bot from taking trades during unpredictable 'flash crash' events.
    """
    def __init__(self, rpc_url="https://polygon-bor.publicnode.com"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.MAX_SAFE_GAS_PRICE_GWEI = 500 # 500 Gwei limit for Polygon
        
    def check_network_health(self):
        """
        Returns (is_safe: bool, reason: str)
        """
        print("🛡️ [Risk Manager] Scanning network health & gas levels...")
        try:
            current_gas_price_wei = self.w3.eth.gas_price
            current_gas_price_gwei = self.w3.from_wei(current_gas_price_wei, 'gwei')
            
            print(f"⛽ [Risk Manager] Current Gas Price: {current_gas_price_gwei:.2f} Gwei")
            
            if current_gas_price_gwei > self.MAX_SAFE_GAS_PRICE_GWEI:
                print("🚨 [Risk Manager] EXTREME GAS SPIKE DETECTED! Initiating SLEEP MODE.")
                return False, "SLEEP_MODE: High Gas"
                
            # Here we could also check block time delays, missing blocks, etc.
            # But for MVP, gas spike is the biggest MEV risk (e.g. during a bot war or NFT mint)
            print("✅ [Risk Manager] Network is Stable. All systems GO.")
            return True, "SAFE"
            
        except Exception as e:
            print(f"⚠️ [Risk Manager] Network check failed: {e}")
            return False, "SLEEP_MODE: Network Error"

if __name__ == "__main__":
    risk_manager = RiskManager()
    safe, status = risk_manager.check_network_health()
    print(f"Final Status: {status}")
