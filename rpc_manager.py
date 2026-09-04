import time
import asyncio
import aiohttp
import sys

sys.stdout.reconfigure(encoding='utf-8')

class PredictiveRPCManager:
    """
    Tests latency across multiple RPC endpoints and routes traffic to the fastest one
    to ensure we never miss a block in the Dark Forest.
    """
    def __init__(self):
        self.polygon_rpcs = [
            "https://polygon-bor.publicnode.com",
            "https://polygon-rpc.com",
            "https://rpc-mainnet.maticvigil.com"
        ]
        
    async def measure_latency(self, session, url):
        start = time.time()
        payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
        try:
            async with session.post(url, json=payload, timeout=2) as resp:
                if resp.status == 200:
                    return time.time() - start
                return float('inf')
        except:
            return float('inf')

    async def get_best_rpc(self):
        print("🌐 [RPC Manager] Pinging network nodes for optimal routing...")
        async with aiohttp.ClientSession() as session:
            tasks = [self.measure_latency(session, url) for url in self.polygon_rpcs]
            results = await asyncio.gather(*tasks)
            
            best_idx = results.index(min(results))
            best_rpc = self.polygon_rpcs[best_idx]
            latency = results[best_idx]
            
            if latency == float('inf'):
                print("🚨 [RPC Manager] CRITICAL ERROR: All RPCs are down!")
                return None
                
            print(f"⚡ [RPC Manager] Selected {best_rpc} (Latency: {latency*1000:.0f}ms)")
            return best_rpc

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    manager = PredictiveRPCManager()
    asyncio.run(manager.get_best_rpc())
