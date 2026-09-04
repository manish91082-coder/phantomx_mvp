import os
import sys
import json
import asyncio
import aiohttp
import solcx
from web3 import Web3

sys.stdout.reconfigure(encoding='utf-8')

# Install specific solc version if not present
SOLC_VERSION = '0.8.20'
if SOLC_VERSION not in solcx.get_installed_solc_versions():
    print(f"📥 Installing solc v{SOLC_VERSION}...")
    solcx.install_solc(SOLC_VERSION)

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

async def execute_dry_run_intent(abi, bytecode, rpc_url):
    print("🚀 Preparing Raw Transaction Intent (State Override Dry Run)...")
    
    w3 = Web3()
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # 1. Encode the function call (executeArbitrage with 1 WETH)
    # 1 WETH = 10**18
    trade_size = 1 * (10**18)
    encoded_data = contract.encode_abi("executeArbitrage", args=[trade_size])
    
    # 2. Setup the "Phantom Address" where we inject our code for the Dry Run
    phantom_address = "0x0000000000000000000000000000000000001337"
    caller_address = "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B" # Arbitrary EOA
    
    # 3. QuickSwap V2 Pool State Override (God Mode)
    quickswap_pool = "0x853Ee4b2A13f8a742d64C8F088bE7bA2131f670d"
    usdc_contract = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    weth_contract = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
    
    # Original slot 8 (reserves + timestamp)
    # We double the reserve0 (USDC) from 0x1091da5237e (1.13M) to 0x2123B4A46FC (2.27M)
    new_reserve0_int = 1138663695230 * 2
    new_reserve0 = hex(new_reserve0_int)[2:].zfill(28) # 112 bits = 28 hex chars
    new_reserve1 = "000000000018aabef7b777216180" # Unchanged WETH reserve
    new_timestamp = "6a9a231d" # Unchanged
    fake_slot_8 = "0x" + new_timestamp + new_reserve1 + new_reserve0
    
    # USDC BalanceOf Slot for Quickswap Pool
    usdc_balance_slot = "0x4e0a4827fcbc6067294395cb76e48f4ec8bf446ce26210bc37cd89c51f3b17db"
    new_usdc_balance = hex(new_reserve0_int)
    new_usdc_balance_padded = "0x" + new_usdc_balance[2:].zfill(64)

    # WETH BalanceOf Slot for Phantom Address
    phantom_weth_slot = Web3.to_hex(Web3().keccak(hexstr=phantom_address.replace("0x", "").zfill(64) + "0000000000000000000000000000000000000000000000000000000000000000"))
    phantom_weth_balance = hex(10 * 10**18) # 10 WETH
    phantom_weth_balance_padded = "0x" + phantom_weth_balance[2:].zfill(64)
    
    print(f"fake_slot_8 length: {len(fake_slot_8)}")
    print(f"usdc_balance_slot length: {len(usdc_balance_slot)}")
    print(f"new_usdc_balance_padded length: {len(new_usdc_balance_padded)}")
    print(f"phantom_weth_slot length: {len(phantom_weth_slot)}")
    print(f"phantom_weth_balance_padded length: {len(phantom_weth_balance_padded)}")

    # 4. Construct Raw JSON-RPC for eth_call with State Override
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
                },
                quickswap_pool: {
                    "stateDiff": {
                        "0x0000000000000000000000000000000000000000000000000000000000000008": fake_slot_8
                    }
                },
                usdc_contract: {
                    "stateDiff": {
                        usdc_balance_slot: new_usdc_balance_padded
                    }
                },
                weth_contract: {
                    "stateDiff": {
                        phantom_weth_slot: phantom_weth_balance_padded
                    }
                }
            }
        ],
        "id": 1
    }
    
    print(f"📡 Sending Intent to {rpc_url}...")
    async with aiohttp.ClientSession() as session:
        async with session.post(rpc_url, json=payload) as response:
            result = await response.json()
            
            print("\n================ DRY RUN RESULTS ================")
            if "error" in result:
                err_msg = result['error'].get('message', 'Unknown Error')
                print(f"🔴 EVM REVERT DETECTED!")
                print(f"❌ Reason: {err_msg}")
                if "Arbitrage Unprofitable! Reverting..." in err_msg or "execution reverted" in err_msg:
                    print("🛡️ Zero-Loss Formula successfully blocked a bad trade at the EVM level!")
            else:
                print(f"🟢 SUCCESS! EVM executed the arbitrage without reverting!")
                print(f"Return Data: {result['result']}")
            print("=================================================")
            
            with open('dry_run_results.json', 'w') as f:
                json.dump(result, f, indent=4)

async def main():
    try:
        abi, bytecode = compile_contract()
    except Exception as e:
        print(f"❌ Compilation Failed: {e}")
        return

    # Fetch Best RPC from .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    rpc_url = "https://polygon-bor.publicnode.com"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("POLYGON_RPC_URL_1="):
                    rpc_url = line.strip().split("=")[1]
                    break
                    
    await execute_dry_run_intent(abi, bytecode, rpc_url)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
