import os
import sys
import asyncio
import aiohttp
import time
import solcx
import json
from web3 import Web3
from eth_abi import decode
from eth_account import Account
from ai_brain import PhantomAIBrain

sys.stdout.reconfigure(encoding='utf-8')

print("🦅 Booting PhantomX Ground Reality Execution Engine (DARK FOREST EDITION)...")

SOLC_VERSION = '0.8.20'

MULTICALL3 = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QUICKSWAP_FACTORY = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UNISWAP_V3_FACTORY = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")

TARGET_TOKENS = {
    "WETH": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"),
    "WMATIC": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"),
    "WBTC": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"),
}

MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]

w3 = Web3(Web3.HTTPProvider("https://polygon-bor.publicnode.com"))
multicall_contract = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
qs_factory = w3.eth.contract(address=QUICKSWAP_FACTORY, abi=QS_FACTORY_ABI)
uv3_factory = w3.eth.contract(address=UNISWAP_V3_FACTORY, abi=UV3_FACTORY_ABI)
qs_pair_template = w3.eth.contract(abi=QS_PAIR_ABI)
uv3_pool_template = w3.eth.contract(abi=UV3_POOL_ABI)

discovered_pairs = {}

# Mock Wallet for testing without real private key
mock_account = Account.create()
print(f"🔐 Initialized Local Signer Wallet: {mock_account.address}")

def compile_contract():
    print("⚙️ Compiling PhantomXMVP.sol with Real Execution Logic...")
    contract_path = os.path.join(os.path.dirname(__file__), 'contracts', 'src', 'PhantomXMVP.sol')
    with open(contract_path, 'r') as f:
        source = f.read()
    compiled = solcx.compile_source(
        source,
        output_values=['abi', 'bin-runtime', 'bin'],
        solc_version=SOLC_VERSION
    )
    contract_id, contract_interface = compiled.popitem()
    return contract_interface['abi'], contract_interface['bin-runtime'], contract_interface['bin']

async def rpc_call(session, url, payload):
    async with session.post(url, json=payload) as resp:
        return await resp.json()

async def prepare_real_transaction(abi, bytecode, bytecode_init, symbol, token_address, startQuickswap, optimal_loan, mev_bribe_usdc, amountOutMin1, amountOutMin2):
    print(f"\n🚨🚨 FLASHBOTS: Executing Dark Forest Arbitrage for {symbol}! 🚨🚨")
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    trade_size = int(optimal_loan * 1e6) # Dynamic USDC loan size
    
    encoded_data = contract.encode_abi("executeArbitrage", args=[USDC, token_address, trade_size, startQuickswap, amountOutMin1, amountOutMin2])
    
    phantom_address = Web3.to_checksum_address("0x0000000000000000000000000000000000001337")
    
    gas_limit = 500000
    
    print("🌍 Fetching Current Network Conditions (Nonce & Gas Price)...")
    base_fee = w3.eth.gas_price
    
    # -------------------------------------------------------------
    # MEV Bribe Conversion (USDC to Native Gas Token wei)
    # -------------------------------------------------------------
    # Roughly: 1 MATIC = $0.50. So bribe_in_matic = mev_bribe_usdc * 2
    bribe_in_native = int((mev_bribe_usdc * 2) * 10**18)
    
    # maxPriorityFeePerGas = Bribe / Gas Limit
    dynamic_priority_fee = int(bribe_in_native / gas_limit)
    # Ensure it's at least 30 gwei
    max_priority_fee = max(dynamic_priority_fee, w3.to_wei(30, 'gwei'))
    max_fee = base_fee + max_priority_fee
    
    nonce = w3.eth.get_transaction_count(mock_account.address)
    
    print("📝 Constructing EIP-1559 Transaction Payload with Dynamic MEV Tip...")
    tx = {
        'type': 2,
        'chainId': 137,
        'to': phantom_address,
        'value': 0,
        'gas': int(gas_limit * 1.2), # 20% buffer
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': nonce,
        'data': encoded_data
    }
    
    print("🔐 Signing Transaction with Private Key...")
    signed_tx = mock_account.sign_transaction(tx)
    raw_tx_hex = signed_tx.raw_transaction.hex()
    
    # -------------------------------------------------------------
    # Dark Forest: Flashbots eth_sendBundle
    # -------------------------------------------------------------
    print("🌑 Packaging into Flashbots/BloXroute Bundle (Private Mempool)...")
    bundle_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_sendBundle",
        "params": [
            {
                "txs": [raw_tx_hex],
                "blockNumber": hex(w3.eth.block_number + 1)
            }
        ]
    }
    
    print(f"✅ Secure Bundle Ready for RPC Dispatch!")
    print(json.dumps(bundle_payload, indent=2))
    print("\n🚀 GROUND REALITY EXECUTION COMPLETE! (Transaction securely built but prevented from broadcasting to avoid real gas fees)")
    print("---------------------------------------------------------------------------")

async def discover_pools(session, rpc_url):
    print("🔍 Discovering Pools...")
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

async def scan_market(session, rpc_url, abi, bytecode, bytecode_init):
    print("\n🚀 Starting Real Execution Engine Scan (Dark Forest Guarded)...")
    symbols = list(discovered_pairs.keys())
    
    brain = PhantomAIBrain()
    
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
        
        response = await rpc_call(session, rpc_url, payload)
        if "result" not in response:
            await asyncio.sleep(1)
            continue
            
        result_data = response["result"]
        decoded_results = decode(["uint256", "bytes[]"], bytes.fromhex(result_data[2:]))
        return_data = decoded_results[1]
        
        idx = 0
        triggered = []
        for symbol in symbols:
            token_address = discovered_pairs[symbol]["token"]
            
            qs_data = return_data[idx]
            qs_price = 0
            qs_usdc_res = 0
            if len(qs_data) >= 96:
                qs_res = decode(["uint112", "uint112", "uint32"], qs_data)
                token0_is_usdc = int(USDC, 16) < int(token_address, 16)
                decimals = {"WBTC": 8}.get(symbol, 18)
                usdc_dec = 1e6
                tok_dec = 10**decimals
                if token0_is_usdc:
                    usdc_res, tok_res = qs_res[0], qs_res[1]
                else:
                    tok_res, usdc_res = qs_res[0], qs_res[1]
                
                qs_usdc_res = usdc_res / usdc_dec
                
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
            
            # Send data to AI Brain
            decision, optimal_loan, guaranteed_profit, mev_bribe = brain.analyze_scenario(qs_price, uv3_price, qs_usdc_res, 0.5)
            
            if decision == "EXECUTE":
                startQuickswap = False if qs_price > uv3_price else True
                
                # Dynamic Slippage Protection - 0.5% max slippage allowed
                # amountOutMin1 and amountOutMin2 calculations:
                # If we start on Quickswap (USDC -> Token -> USDC)
                # First swap out min = (loan / qs_price) * 0.995
                if startQuickswap:
                    amountOutMin1 = int(((optimal_loan / qs_price) * 0.995) * (10**decimals))
                    amountOutMin2 = int((optimal_loan * 1.001) * 1e6) # Require at least 0.1% profit to cover Aave fee
                else:
                    amountOutMin1 = int(((optimal_loan / uv3_price) * 0.995) * (10**decimals))
                    amountOutMin2 = int((optimal_loan * 1.001) * 1e6)
                    
                triggered.append((symbol, token_address, startQuickswap, optimal_loan, mev_bribe, amountOutMin1, amountOutMin2))
            
            idx += 2
            
        for (symbol, token_addr, startQuickswap, optimal_loan, mev_bribe, amountOutMin1, amountOutMin2) in triggered:
            await prepare_real_transaction(abi, bytecode, bytecode_init, symbol, token_addr, startQuickswap, optimal_loan, mev_bribe, amountOutMin1, amountOutMin2)
            return
            
        await asyncio.sleep(2)

async def main():
    rpc_url = "https://polygon-bor.publicnode.com"
    abi, bytecode, bytecode_init = compile_contract()
    async with aiohttp.ClientSession() as session:
        await discover_pools(session, rpc_url)
        await scan_market(session, rpc_url, abi, bytecode, bytecode_init)

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
