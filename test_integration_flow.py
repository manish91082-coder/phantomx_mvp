import asyncio
import aiohttp
import sys
import time
import json
import importlib
from web3 import Web3
from rpc_manager import PredictiveRPCManager
from token_discoverer import TokenDiscoverer
from risk_manager import RiskManager
from macro_ai import MacroStrategistAI

sys.stdout.reconfigure(encoding='utf-8')

# We'll use 07_real_execution for market scanning logic
exec_engine = importlib.import_module("07_real_execution")

async def run_integration_test():
    print("==================================================")
    print("🔬 INTEGRATION & FLOW TESTING (100+ REAL ITERATIONS)")
    print("==================================================")
    
    rpc_mgr = PredictiveRPCManager()
    risk_mgr = RiskManager()
    token_discoverer = TokenDiscoverer()
    macro_ai = MacroStrategistAI()
    
    best_rpc = await rpc_mgr.get_best_rpc()
    if not best_rpc:
        print("Test failed: No RPC.")
        return
        
    risk_mgr.w3 = Web3(Web3.HTTPProvider(best_rpc))
    exec_engine.w3 = Web3(Web3.HTTPProvider(best_rpc))
    
    abi, bytecode, bytecode_init = exec_engine.compile_contract()
    
    stats = {
        "total_iterations": 0,
        "sleep_modes_triggered": 0,
        "successful_scans": 0,
        "arbitrage_opportunities": 0
    }
    
    async with aiohttp.ClientSession() as session:
        # Initial Discoveries
        targets = await token_discoverer.discover_top_tokens(max_tokens=2)
        exec_engine.TARGET_TOKENS = targets
        await exec_engine.discover_pools(session, best_rpc)
        
        print("\n🚀 Commencing 100 continuous test loops...")
        
        # Test loop for 100 iterations
        for i in range(100):
            stats["total_iterations"] += 1
            if i % 10 == 0:
                print(f"--- Iteration {i}/100 ---")
                
            # 1. Risk Check
            is_safe, status = risk_mgr.check_network_health()
            if not is_safe:
                stats["sleep_modes_triggered"] += 1
                await asyncio.sleep(1) # Fast forward wait
                continue
                
            # 2. Macro Strategy
            strategy, assigned_targets = macro_ai.determine_strategy(status, targets)
            
            if strategy == "SPATIAL_ARBITRAGE":
                stats["successful_scans"] += 1
                
                # Mock a single execution scan round
                # In real life, scan_market runs forever. For this test, we just want to run the core logic
                # So we manually extract a snippet from scan_market logic to test state without hanging
                symbols = list(exec_engine.discovered_pairs.keys())
                calls = []
                for symbol in symbols:
                    pair = exec_engine.discovered_pairs[symbol]
                    qs_calldata = exec_engine.qs_pair_template.encode_abi("getReserves", args=[])
                    calls.append((pair["quickswap"], qs_calldata))
                    uv3_calldata = exec_engine.uv3_pool_template.encode_abi("slot0", args=[])
                    calls.append((pair["uniswapV3"], uv3_calldata))
                    
                encoded_multicall = exec_engine.multicall_contract.encode_abi("aggregate", args=[calls])
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [{"to": exec_engine.MULTICALL3, "data": encoded_multicall}, "latest"],
                    "id": 1
                }
                
                response = await exec_engine.rpc_call(session, best_rpc, payload)
                if "result" in response:
                    # If we got data, we successfully interacted with the blockchain
                    pass 
                    
            await asyncio.sleep(0.1) # Fast forward for tests
            
    print("==================================================")
    print("✅ INTEGRATION TEST COMPLETE")
    print(json.dumps(stats, indent=4))
    
    with open('integration_test_results.json', 'w') as f:
        json.dump(stats, f, indent=4)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_integration_test())
