import os
import sys
import asyncio
import aiohttp
import time
import solcx
from web3 import Web3
from eth_abi import decode

sys.stdout.reconfigure(encoding='utf-8')

print("🦅 Booting PhantomX Saturated Engine...")

# Install specific solc version if not present
SOLC_VERSION = '0.8.20'
if SOLC_VERSION not in solcx.get_installed_solc_versions():
    print(f"📥 Installing solc v{SOLC_VERSION}...")
    solcx.install_solc(SOLC_VERSION)

# Constants
MULTICALL3 = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QUICKSWAP_FACTORY = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UNISWAP_V3_FACTORY = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")

TARGET_TOKENS = {
    "WETH": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"),
    "WMATIC": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"),
    "WBTC": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"),
    "LINK": Web3.to_checksum_address("0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39"),
    "USDT": Web3.to_checksum_address("0xc2132D05D31c914a87C6611C10748AEb04B58e8F"),
    "DAI": Web3.to_checksum_address("0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"),
    "AAVE": Web3.to_checksum_address("0xD6DF932A45C0f255f85145f286eA0b292B21C90B"),
    "CRV": Web3.to_checksum_address("0x172370d5Cd63279eFa6d502DAB29171933a610AF"),
    "UNI": Web3.to_checksum_address("0xb33EaAd8d922B1083446DC23f610c2567fB5180f"),
}

MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]

w3 = Web3()
multicall_contract = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
qs_factory = w3.eth.contract(address=QUICKSWAP_FACTORY, abi=QS_FACTORY_ABI)
uv3_factory = w3.eth.contract(address=UNISWAP_V3_FACTORY, abi=UV3_FACTORY_ABI)
qs_pair_template = w3.eth.contract(abi=QS_PAIR_ABI)
uv3_pool_template = w3.eth.contract(abi=UV3_POOL_ABI)

discovered_pairs = {}

# Compilation
def compile_contract():
    print("⚙️ Compiling PhantomXMVP.sol...")
    contract_path = os.path.join(os.path.dirname(__file__), 'contracts', 'src', 'PhantomXMVP.sol')
    with open(contract_path, 'r') as f:
        source = f.read()
    compiled = solcx.compile_source(
        source,
        output_values=['abi', 'bin-runtime'],
        solc_version=SOLC_VERSION
    )
    contract_id, contract_interface = compiled.popitem()
    return contract_interface['abi'], contract_interface['bin-runtime']

async def rpc_call(session, url, payload):
    async with session.post(url, json=payload) as resp:
        return await resp.json()

async def fire_dry_run(session, rpc_url, abi, bytecode, symbol, qs_price, uv3_price, spread_pct):
    print(f"\n🚨🚨 ALERT! {symbol}/USDC Spread detected ({spread_pct:.2f}%)! Firing Dry Run Intent! 🚨🚨")
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    trade_size = 1 * (10**18)
    encoded_data = contract.encode_abi("executeArbitrage", args=[trade_size])
    
    phantom_address = "0x0000000000000000000000000000000000001337"
    caller_address = "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {
                "from": caller_address,
                "to": phantom_address,
                "data": encoded_data
            },
            "latest",
            {
                phantom_address: {
                    "code": "0x" + bytecode
                }
            }
        ],
        "id": 1
    }
    
    start_time = time.time()
    result = await rpc_call(session, rpc_url, payload)
    latency = time.time() - start_time
    
    if "error" in result:
        print(f"🔴 EVM REVERT DETECTED (Dry Run Latency: {latency*1000:.1f}ms)")
        print(f"❌ Reason: {result['error'].get('message', 'Unknown Error')}")
    else:
        print(f"🟢 SUCCESS! EVM simulated arbitrage without reverting! (Dry Run Latency: {latency*1000:.1f}ms)")
        try:
            raw_res = result['result']
            simulated_profit = int(raw_res, 16) / 10**18
            print(f"💸 Net Profit from Simulation: {simulated_profit} WETH")
        except:
            print(f"Raw Result: {result['result']}")
    print("---------------------------------------------------------------------------")

async def discover_pools(session, rpc_url):
    print("🔍 Eagle Eye: Discovering Liquidity Pools via Multicall...")
    calls = []
    symbols = list(TARGET_TOKENS.keys())
    
    for symbol in symbols:
        token_addr = TARGET_TOKENS[symbol]
        qs_calldata = qs_factory.encode_abi("getPair", args=[USDC, token_addr])
        calls.append((QUICKSWAP_FACTORY, qs_calldata))
        
        uv3_calldata = uv3_factory.encode_abi("getPool", args=[USDC, token_addr, 500])
        calls.append((UNISWAP_V3_FACTORY, uv3_calldata))

    encoded_multicall = multicall_contract.encode_abi("aggregate", args=[calls])
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": MULTICALL3, "data": encoded_multicall}, "latest"],
        "id": 1
    }
    
    response = await rpc_call(session, rpc_url, payload)
    if "result" not in response:
        print("❌ Multicall failed:", response)
        return

    result_data = response["result"]
    decoded_results = decode(["uint256", "bytes[]"], bytes.fromhex(result_data[2:]))
    return_data = decoded_results[1]
    
    idx = 0
    for symbol in symbols:
        qs_data = return_data[idx]
        uv3_data = return_data[idx+1]
        
        qs_address = "0x0000000000000000000000000000000000000000"
        uv3_address = "0x0000000000000000000000000000000000000000"
        
        if len(qs_data) >= 32:
            qs_address = Web3.to_checksum_address(decode(["address"], qs_data)[0])
        if len(uv3_data) >= 32:
            uv3_address = Web3.to_checksum_address(decode(["address"], uv3_data)[0])
            
        idx += 2
        
        if qs_address != "0x0000000000000000000000000000000000000000" and uv3_address != "0x0000000000000000000000000000000000000000":
            discovered_pairs[symbol] = {
                "quickswap": qs_address,
                "uniswapV3": uv3_address,
                "token": TARGET_TOKENS[symbol]
            }
            print(f"✅ Found {symbol}/USDC -> QS: {qs_address[:8]}... UV3: {uv3_address[:8]}...")
        else:
            print(f"⚠️ Missing liquidity for {symbol}/USDC. Skipping.")

async def scan_market(session, rpc_url, abi, bytecode):
    print("\n🚀 Initiating Infinite Saturated Engine Scan...")
    symbols = list(discovered_pairs.keys())
    
    while True:
        calls = []
        for symbol in symbols:
            pair = discovered_pairs[symbol]
            qs_calldata = qs_pair_template.encode_abi("getReserves", args=[])
            calls.append((pair["quickswap"], qs_calldata))
            
            uv3_calldata = uv3_pool_template.encode_abi("slot0", args=[])
            calls.append((pair["uniswapV3"], uv3_calldata))

        encoded_multicall = multicall_contract.encode_abi("aggregate", args=[calls])
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{"to": MULTICALL3, "data": encoded_multicall}, "latest"],
            "id": 1
        }
        
        start_time = time.time()
        response = await rpc_call(session, rpc_url, payload)
        latency = time.time() - start_time
        
        if "result" not in response:
            await asyncio.sleep(1)
            continue
            
        result_data = response["result"]
        decoded_results = decode(["uint256", "bytes[]"], bytes.fromhex(result_data[2:]))
        return_data = decoded_results[1]
        
        print(f"\n\n🦅 PhantomX Eagle Eye Multi-Pair Scanner")
        print(f"⏱️ Network Latency: {latency*1000:.1f}ms | Block: {decoded_results[0]}")
        print("-" * 75)
        print(f"{'PAIR':<12} | {'QUICKSWAP PRICE':<18} | {'UNISWAP V3 PRICE':<18} | {'SPREAD (PROFIT)':<15}")
        print("-" * 75)
        
        idx = 0
        triggered_dry_runs = []
        for symbol in symbols:
            token_address = discovered_pairs[symbol]["token"]
            
            qs_data = return_data[idx]
            qs_price = 0
            if len(qs_data) >= 96:
                qs_res = decode(["uint112", "uint112", "uint32"], qs_data)
                token0_is_usdc = int(USDC, 16) < int(token_address, 16)
                token_decimals = {"WBTC": 8, "USDT": 6, "USDC": 6}
                decimals = token_decimals.get(symbol, 18)
                usdc_dec = 1e6
                tok_dec = 10**decimals
                if token0_is_usdc:
                    usdc_res, tok_res = qs_res[0], qs_res[1]
                else:
                    tok_res, usdc_res = qs_res[0], qs_res[1]
                if tok_res > 0:
                    qs_price = (usdc_res / usdc_dec) / (tok_res / tok_dec)
                    
            uv3_data = return_data[idx+1]
            uv3_price = 0
            if len(uv3_data) >= 224:
                uv3_res = decode(["uint160", "int24", "uint16", "uint16", "uint16", "uint8", "bool"], uv3_data)
                sqrtPriceX96 = uv3_res[0]
                if sqrtPriceX96 > 0:
                    price_ratio = (sqrtPriceX96 / (2**96)) ** 2
                    if token0_is_usdc:
                        uv3_price = price_ratio * (tok_dec / usdc_dec)
                    else:
                        uv3_price = (1 / price_ratio) * (tok_dec / usdc_dec)
            
            spread = abs(qs_price - uv3_price)
            spread_pct = (spread / max(qs_price, 1)) * 100
            
            color = "\033[92m" if spread_pct > 0.05 else "\033[90m"
            reset = "\033[0m"
            print(f"{color}{symbol}/USDC   | ${qs_price:<17.4f} | ${uv3_price:<17.4f} | ${spread:.4f} ({spread_pct:.2f}%){reset}")
            
            if spread_pct > 0.05:
                triggered_dry_runs.append((symbol, qs_price, uv3_price, spread_pct))
            
            idx += 2
            
        print("-" * 75)
        
        # Fire Dry Runs concurrently for all pairs that crossed the threshold
        for (symbol, qs_price, uv3_price, spread_pct) in triggered_dry_runs:
            await fire_dry_run(session, rpc_url, abi, bytecode, symbol, qs_price, uv3_price, spread_pct)
        
        print("⚡ Zero-Loss Formula Engine Active... Scanning every 2 seconds...")
        await asyncio.sleep(2)

async def main():
    rpc_url = "https://polygon-bor.publicnode.com"
    abi, bytecode = compile_contract()
    async with aiohttp.ClientSession() as session:
        await discover_pools(session, rpc_url)
        await scan_market(session, rpc_url, abi, bytecode)

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
