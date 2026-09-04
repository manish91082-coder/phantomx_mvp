import sys

sys.stdout.reconfigure(encoding='utf-8')

class MacroStrategistAI:
    """
    The General. Determines the macro strategy (e.g. Spatial vs Sandwich vs Triangular).
    For MVP, it prioritizes the highest volume tokens discovered and assigns them to the Micro AI (ai_brain).
    """
    def __init__(self):
        self.current_strategy = "SPATIAL_ARBITRAGE"
        
    def determine_strategy(self, network_status, discovered_tokens):
        print(f"\n🧠 [Macro AI] Analyzing Market Conditions...")
        
        if network_status != "SAFE":
            print(f"🛑 [Macro AI] Risk Manager flagged '{network_status}'. Strategy: SLEEP_MODE.")
            return "SLEEP_MODE", {}

        if not discovered_tokens:
            print("🛑 [Macro AI] No targets found. Strategy: WAIT.")
            return "WAIT", {}
            
        print(f"🎯 [Macro AI] Network is SAFE. Selected Strategy: {self.current_strategy}")
        print(f"🎯 [Macro AI] Assigned {len(discovered_tokens)} targets to Micro AI for execution.")
        
        return self.current_strategy, discovered_tokens

if __name__ == "__main__":
    macro = MacroStrategistAI()
    macro.determine_strategy("SAFE", {"LINK": "0x123", "UNI": "0x456"})
