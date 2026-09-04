import asyncio
import sys
import importlib
from rpc_manager import PredictiveRPCManager
from token_discoverer import TokenDiscoverer
from risk_manager import RiskManager
from macro_ai import MacroStrategistAI

sys.stdout.reconfigure(encoding='utf-8')

print("\n🚀🚀🚀 INITIALIZING PHANTOM-X: GUIDED MISSILE AGI SYSTEM 🚀🚀🚀\n")

async def run_missile():
    # 1. Boot up subsystems
    rpc_mgr = PredictiveRPCManager()
    risk_mgr = RiskManager()
    token_discoverer = TokenDiscoverer()
    macro_ai = MacroStrategistAI()
    
    # 2. Network Routing
    best_rpc = await rpc_mgr.get_best_rpc()
    if not best_rpc:
        print("❌ [Guided Missile] Cannot proceed without a valid RPC. Aborting.")
        return
        
    risk_mgr.w3 = __import__('web3').Web3(__import__('web3').Web3.HTTPProvider(best_rpc))
    
    # 3. Main Operational Loop
    while True:
        # Step A: Risk Check
        is_safe, status = risk_mgr.check_network_health()
        if not is_safe:
            print(f"💤 [Guided Missile] Standing down. Reason: {status}")
            await asyncio.sleep(10)
            continue
            
        # Step B: Autonomous Token Discovery
        targets = await token_discoverer.discover_top_tokens(max_tokens=3)
        
        # Step C: Macro Strategy
        strategy, assigned_targets = macro_ai.determine_strategy(status, targets)
        
        if strategy == "SLEEP_MODE" or strategy == "WAIT":
            await asyncio.sleep(5)
            continue
            
        # Step D: Execute Strategy (Micro AI Hand-off)
        if strategy == "SPATIAL_ARBITRAGE":
            print(f"🔥 [Guided Missile] Handing off to Execution Engine with {len(assigned_targets)} dynamic targets...")
            
            # We import the real execution engine and override its targets dynamically!
            exec_engine = importlib.import_module("07_real_execution")
            exec_engine.TARGET_TOKENS = assigned_targets
            exec_engine.w3 = __import__('web3').Web3(__import__('web3').Web3.HTTPProvider(best_rpc))
            
            abi, bytecode, bytecode_init = exec_engine.compile_contract()
            async with __import__('aiohttp').ClientSession() as session:
                await exec_engine.discover_pools(session, best_rpc)
                
                # Run the scanner for a limited time (e.g., 5 iterations) then re-evaluate macro strategy
                print("⏱️ [Guided Missile] Commencing micro-execution phase (5 sweeps)...")
                # We modify the infinite loop in 07_real_execution just for demonstration, 
                # but since it's hardcoded to While True, we'll just run it. 
                # Ideally, it would yield back to the orchestrator. For MVP, we let it scan.
                try:
                    await asyncio.wait_for(exec_engine.scan_market(session, best_rpc, abi, bytecode, bytecode_init), timeout=15.0)
                except asyncio.TimeoutError:
                    print("🔄 [Guided Missile] Micro-execution sweep complete. Returning to Macro Strategist for reassessment.")
                    
        # Sleep before next macro cycle
        await asyncio.sleep(5)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(run_missile())
    except KeyboardInterrupt:
        print("\n🛑 [Guided Missile] Shutdown signal received. Disengaging.")
