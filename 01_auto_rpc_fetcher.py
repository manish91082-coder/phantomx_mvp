import asyncio
import json
import time
import os
import sys
import aiohttp
from typing import List, Dict

sys.stdout.reconfigure(encoding='utf-8')

# The Ultimate Offline List of Polygon RPCs for Zero-Latency Discovery
POLYGON_RPCS = [
    "https://polygon-rpc.com",
    "https://rpc-mainnet.matic.network",
    "https://rpc-mainnet.maticvigil.com",
    "https://rpc-mainnet.matic.quiknode.pro",
    "https://matic-mainnet.chainstacklabs.com",
    "https://matic-mainnet-full-rpc.bwarelabs.com",
    "https://polygon-bor.publicnode.com",
    "https://1rpc.io/matic",
    "https://polygon.llamarpc.com",
    "https://polygon.rpc.blxrbdn.com",
    "https://api.zan.top/node/ws/v1/polygon/mainnet/public",
    "https://polygon.mevblocker.io",
    "https://polygon-mainnet.public.blastapi.io",
    "https://rpc.ankr.com/polygon",
    "https://polygon.api.onfinality.io/public",
    "https://drpc.org/ogrpc/polygon",
    "https://rpc.payload.de/polygon",
    "https://polygon.gateway.tenderly.co",
    "https://gateway.pinata.cloud/v1/rpc/polygon",
    "https://polygon-mainnet.rpcfast.com",
    "https://polygon.blockpi.network/v1/rpc/public",
    "https://rpc.public.zkevm-test.net", # Just in case, let it fail
    "https://api.securerpc.com/v1/polygon",
    "https://mainnet.era.zksync.io", # Invalid but added for robust testing
    "https://endpoints.omniatech.io/v1/matic/mainnet/public",
    "https://public.stackup.sh/api/v1/node/polygon-mainnet",
    "https://rpc-polygon.bnb48.club",
    "https://polygon-mainnet.g.alchemy.com/v2/demo",
    "https://polygon-mainnet.infura.io/v3/demo"
]

ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), ".env")

async def test_rpc(session: aiohttp.ClientSession, url: str) -> Dict:
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }
    start_time = time.time()
    try:
        # Strict 2 second timeout for Nano-second optimization
        async with session.post(url, json=payload, timeout=2.0) as response:
            if response.status == 200:
                data = await response.json()
                latency = time.time() - start_time
                if "result" in data:
                    block_number = int(data["result"], 16)
                    return {"url": url, "latency": latency, "block": block_number, "status": "success"}
    except Exception:
        pass
    return {"url": url, "latency": float('inf'), "block": 0, "status": "failed"}

async def main():
    print("🚀 PhantomX: Executing Offline RPC Discovery (Zero-Latency Rule)...")
    print(f"📡 Pinging {len(POLYGON_RPCS)} RPCs concurrently...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [test_rpc(session, rpc) for rpc in POLYGON_RPCS]
        results = await asyncio.gather(*tasks)

    # Filter successful ones
    success_rpcs = [r for r in results if r["status"] == "success"]
    
    if not success_rpcs:
        print("❌ All public RPCs failed. Please check network connection.")
        return

    # Sort by highest block number (to avoid stale nodes), then by lowest latency
    max_block = max(r["block"] for r in success_rpcs)
    # Consider any node within 3 blocks of max_block as healthy, then sort by latency
    healthy_rpcs = [r for r in success_rpcs if r["block"] >= max_block - 3]
    healthy_rpcs.sort(key=lambda x: x["latency"])

    best_rpc = healthy_rpcs[0]
    print(f"✅ Best RPC found out of {len(success_rpcs)} successful connections: {best_rpc['url']}")
    print(f"📊 Latency: {best_rpc['latency']:.4f}s | Block: {best_rpc['block']}")

    # Save all healthy RPCs to .env for the RPC Manager to use as fallbacks
    env_content = ""
    for i, rpc in enumerate(healthy_rpcs[:5]): # Save top 5
        env_content += f"POLYGON_RPC_URL_{i+1}={rpc['url']}\n"
    
    # Read existing .env if any
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, "r") as f:
            lines = f.readlines()
        # Remove existing POLYGON_RPC_URLs
        lines = [l for l in lines if not l.startswith("POLYGON_RPC_URL")]
        lines.append(env_content)
        final_content = "".join(lines)
    else:
        final_content = env_content

    with open(ENV_FILE_PATH, "w") as f:
        f.write(final_content)
    print(f"💾 Saved Top 5 Ultra-Fast RPCs to {ENV_FILE_PATH}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
