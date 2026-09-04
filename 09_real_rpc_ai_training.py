import os
import sys
import asyncio
import aiohttp
import time
import json
from web3 import Web3
from eth_abi import decode
from eth_account import Account
from rpc_manager import RPCManager
from ai_brain import PhantomAIBrain

sys.stdout.reconfigure(encoding='utf-8')

MULTICALL3 = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QUICKSWAP_FACTORY = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UNISWAP_V3_FACTORY = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")

DISCOVERED_PAIRS = {
    'WETH': {'quickswap': '0x853Ee4b2A13f8a742d64C8F088bE7bA2131f670d', 'uniswapV3': '0x45dDa9cb7c25131DF268515131f647d726f50608', 'token': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'}, 
    'WMATIC': {'quickswap': '0x6e7a5FAFcec6BB1e78bAE2A1F0B612012BF14827', 'uniswapV3': '0xA374094527e1673A86dE625aa59517c5dE346d32', 'token': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'}, 
}

w3 = Web3()
qs_pair_template = w3.eth.contract(abi=[{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}])
uv3_pool_template = w3.eth.contract(abi=[{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}])
multicall_contract = w3.eth.contract(address=MULTICALL3, abi=[{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}])

def calculate_true_outcome(qs_price, uv3_price, qs_usdc_reserves, gas_fee_usdc, optimal_loan):
    if optimal_loan == 0:
        return 0
    spread = abs(qs_price - uv3_price)
    spread_pct = spread / max(qs_price, 1)
    gross_profit = spread_pct * optimal_loan
    actual_slippage = optimal_loan * (optimal_loan / max(qs_usdc_reserves, 1)) # Dynamic realistic slippage
    net_profit = gross_profit - gas_fee_usdc - actual_slippage
    return net_profit

async def train_on_real_rpc():
    print("🚀 Booting Real RPC AI Training Engine (Dynamic Flash Loans)...")
    rpc_manager = RPCManager()
    brain = PhantomAIBrain()
    
    log_file = "training_log_v2.jsonl"
    if os.path.exists(log_file):
        os.remove(log_file)
        
    print("🔄 Rule: Must achieve 10,000 consecutive perfect decisions to saturate.\n")
    
    start_time = time.time()
    total_processed = 0
    
    async with aiohttp.ClientSession() as session:
        while brain.consecutive_correct < 10000:
            total_processed += 1
            calls = []
            symbols = list(DISCOVERED_PAIRS.keys())
            for symbol in symbols:
                pair = DISCOVERED_PAIRS[symbol]
                qs_calldata = qs_pair_template.encode_abi("getReserves", args=[])
                calls.append((Web3.to_checksum_address(pair["quickswap"]), qs_calldata))
                uv3_calldata = uv3_pool_template.encode_abi("slot0", args=[])
                calls.append((Web3.to_checksum_address(pair["uniswapV3"]), uv3_calldata))

            encoded_multicall = multicall_contract.encode_abi("aggregate", args=[calls])
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{"to": MULTICALL3, "data": encoded_multicall}, "latest"],
                "id": total_processed
            }
            
            response = await rpc_manager.call(session, payload)
            if not response or "result" not in response:
                await asyncio.sleep(1)
                continue
                
            result_data = response["result"]
            decoded_results = decode(["uint256", "bytes[]"], bytes.fromhex(result_data[2:]))
            return_data = decoded_results[1]
            
            qs_data = return_data[0]
            uv3_data = return_data[1]
            
            qs_price, qs_usdc_reserves = 0, 0
            if len(qs_data) >= 96:
                qs_res = decode(["uint112", "uint112", "uint32"], qs_data)
                usdc_res, tok_res = qs_res[0], qs_res[1]
                if tok_res > 0:
                    qs_price = (usdc_res / 1e6) / (tok_res / 10**18)
                    qs_usdc_reserves = usdc_res / 1e6
                    
            uv3_price = 0
            if len(uv3_data) >= 224:
                uv3_res = decode(["uint160", "int24", "uint16", "uint16", "uint16", "uint8", "bool"], uv3_data)
                sqrtPriceX96 = uv3_res[0]
                if sqrtPriceX96 > 0:
                    price_ratio = (sqrtPriceX96 / (2**96)) ** 2
                    uv3_price = price_ratio * (10**18 / 1e6)
            
            # Simulated gas fetch for speed, fallback to 30 gwei equivalent
            gas_fee_usdc = 0.05 
            
            # --- AI EVALUATION (Dynamic) ---
            decision, optimal_loan, expected_profit = brain.analyze_scenario(qs_price, uv3_price, qs_usdc_reserves, gas_fee_usdc)
            true_net_profit = calculate_true_outcome(qs_price, uv3_price, qs_usdc_reserves, gas_fee_usdc, optimal_loan)
            
            is_correct = False
            # If AI said EXECUTE, true profit MUST be > 0
            if decision == "EXECUTE" and true_net_profit > 0.05:
                is_correct = True
            # If AI said WAIT/IGNORE, true profit MUST be <= 0.05
            elif decision in ["WAIT", "IGNORE"] and true_net_profit <= 0.05:
                is_correct = True
                
            if not is_correct:
                print(f"❌ MISTAKE DETECTED! Resetting consecutive counter from {brain.consecutive_correct} to 0.")
                brain.update_weights(true_net_profit, expected_profit)
                
            brain.record_result(is_correct)
            
            log_entry = {
                "iteration": total_processed,
                "qs_price": qs_price,
                "uv3_price": uv3_price,
                "optimal_loan": optimal_loan,
                "decision": decision,
                "expected": expected_profit,
                "actual": true_net_profit,
                "correct": is_correct,
                "consecutive": brain.consecutive_correct
            }
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
            if total_processed % 100 == 0:
                print(f"🔄 Total Fetches: {total_processed} | Consecutive Perfect: {brain.consecutive_correct}/10000 | AI Weights: {brain.weights['gas_penalty']:.2f}")

    elapsed = time.time() - start_time
    print("\n=================================================")
    print("🏆 REAL RPC AI TRAINING FINAL SATURATION COMPLETE 🏆")
    print(f"⏱️ Training Time: {elapsed:.2f} seconds")
    print(f"🎯 Successfully hit 10,000 consecutive perfect dynamic decisions!")
    print(f"⚖️ Final AI Weights: {brain.weights}")
    
if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(train_on_real_rpc())
