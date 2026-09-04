import os
import asyncio
import json
import sys
from web3 import AsyncWeb3
from rpc_manager import RPCManager

sys.stdout.reconfigure(encoding='utf-8')

# --- Addresses on Polygon ---
USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174" # 6 decimals
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619" # 18 decimals

# QuickSwap V2 Pool for USDC/WETH
QUICKSWAP_V2_POOL = "0x853Ee4b2A13f8a742d64C8F088bE7bA2131f670d"
# Uniswap V3 Pool for USDC/WETH (500 fee / 0.05%)
UNISWAP_V3_POOL = "0x45dDa9cb7c25131DF268515131f647d726f50608"
# Aave V3 Pool (Polygon) for Flash Loans
AAVE_V3_POOL = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"

# --- ABIs ---
V2_PAIR_ABI = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}]')

V3_POOL_ABI = json.loads('[{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')

AAVE_V3_ABI = json.loads('[{"inputs":[],"name":"FLASHLOAN_PREMIUM_TOTAL","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"}]')

async def main():
    print("🚀 PhantomX MVP: Golden Vertical Slice (Continuous Scanner)")
    print("---------------------------------------------------------")
    
    # 1. Setup RPC Manager
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    urls = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("POLYGON_RPC_URL"):
                    urls.append(line.strip().split("=")[1])
    
    if not urls:
        urls = ["https://polygon-bor.publicnode.com"]
        
    manager = RPCManager(urls, penalty_seconds=10)
    w3 = await manager.get_web3()
    print(f"✅ Connected to Polygon via: {w3.provider.endpoint_uri}")
    
    quickswap_contract = w3.eth.contract(address=w3.to_checksum_address(QUICKSWAP_V2_POOL), abi=V2_PAIR_ABI)
    uniswap_contract = w3.eth.contract(address=w3.to_checksum_address(UNISWAP_V3_POOL), abi=V3_POOL_ABI)
    aave_contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_V3_POOL), abi=AAVE_V3_ABI)
    
    print("\n⏳ Entering Infinite Loop. Scanning for Arbitrage every 2 seconds...")
    scan_count = 0
    
    while True:
        try:
            scan_count += 1
            start_time = time.time()
            
            # Use gather to fetch data concurrently to save milliseconds
            reserves_task = quickswap_contract.functions.getReserves().call()
            t0_qs_task = quickswap_contract.functions.token0().call()
            slot0_task = uniswap_contract.functions.slot0().call()
            t0_uni_task = uniswap_contract.functions.token0().call()
            fee_task = aave_contract.functions.FLASHLOAN_PREMIUM_TOTAL().call()
            gas_price_task = w3.eth.gas_price
            
            results = await asyncio.gather(
                reserves_task, t0_qs_task, slot0_task, t0_uni_task, fee_task, gas_price_task
            )
            
            reserves, t0_addr, slot0, t0_addr_v3, fee_premium, gas_price_wei = results
            
            # --- QuickSwap V2 Math ---
            if t0_addr.lower() == USDC.lower():
                usdc_reserve = reserves[0] / 1e6
                weth_reserve = reserves[1] / 1e18
            else:
                usdc_reserve = reserves[1] / 1e6
                weth_reserve = reserves[0] / 1e18
                
            quickswap_price = usdc_reserve / weth_reserve if weth_reserve > 0 else 0
            
            # --- Uniswap V3 Math ---
            sqrtPriceX96 = slot0[0]
            price_ratio = (sqrtPriceX96 / (2**96)) ** 2
            
            if t0_addr_v3.lower() == USDC.lower():
                uniswap_price = (1 / price_ratio) * (1e18 / 1e6)
            else:
                uniswap_price = price_ratio * (1e6 / 1e18)
                
            # --- Spread & Fee ---
            spread = abs(quickswap_price - uniswap_price)
            spread_pct = (spread / min(quickswap_price, uniswap_price)) * 100
            fee_pct = fee_premium / 10000
            
            # --- Gas & Zero-Loss Math ---
            estimated_gas_limit = 400000 
            gas_cost_matic = (gas_price_wei * estimated_gas_limit) / 1e18
            MATIC_PRICE_USDC = 0.45 
            gas_cost_usdc = gas_cost_matic * MATIC_PRICE_USDC
            
            TRADE_SIZE_WETH = 1.0
            amount_in_with_fee = TRADE_SIZE_WETH * 0.997 
            expected_usdc_out = (usdc_reserve * amount_in_with_fee) / (weth_reserve + amount_in_with_fee)
            actual_price_received = expected_usdc_out / TRADE_SIZE_WETH
            slippage_usdc = (quickswap_price - actual_price_received) * TRADE_SIZE_WETH
            
            gross_spread_usdc = spread * TRADE_SIZE_WETH
            flash_fee_usdc = TRADE_SIZE_WETH * uniswap_price * (fee_pct / 100) 
            
            net_profit_usdc = gross_spread_usdc - flash_fee_usdc - gas_cost_usdc - slippage_usdc
            
            elapsed = time.time() - start_time
            
            sys.stdout.write(f"\r[Scan #{scan_count}] {elapsed:.3f}s | QS: ${quickswap_price:.2f} | Uni: ${uniswap_price:.2f} | Spread: ${spread:.2f} ({spread_pct:.3f}%) | Net Profit: ${net_profit_usdc:.4f}    ")
            sys.stdout.flush()
            
            if net_profit_usdc > 0:
                print(f"\n🟢 [ALERT] PROFITABLE ARBITRAGE DETECTED! Net Profit: ${net_profit_usdc:.4f} --> Triggering Dry Run Intent...")
                # TODO: Trigger Intent (Task 2.8)
                break
                
            await asyncio.sleep(2) # 2 seconds delay to avoid rate limiting
            
        except Exception as e:
            print(f"\n⚠️ Error during scan: {e}. Rotating RPC...")
            w3 = await manager.get_web3()
            quickswap_contract = w3.eth.contract(address=w3.to_checksum_address(QUICKSWAP_V2_POOL), abi=V2_PAIR_ABI)
            uniswap_contract = w3.eth.contract(address=w3.to_checksum_address(UNISWAP_V3_POOL), abi=V3_POOL_ABI)
            aave_contract = w3.eth.contract(address=w3.to_checksum_address(AAVE_V3_POOL), abi=AAVE_V3_ABI)
            await asyncio.sleep(2)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
