import sys
import asyncio
import aiohttp
from web3 import Web3

sys.stdout.reconfigure(encoding='utf-8')

class TokenDiscoverer:
    """
    Scans the market (via public API like DexScreener) to automatically find
    trending, high-volume tokens for the Guided Missile to target.
    """
    def __init__(self, chain="polygon"):
        self.chain = chain
        self.dexscreener_url = f"https://api.dexscreener.com/latest/dex/search?q={chain}"
        
    async def discover_top_tokens(self, max_tokens=3):
        """
        Fetches top tokens by volume/liquidity on the specified chain.
        Returns a dictionary of symbol: address
        """
        print(f"📡 [Token Discoverer] Scanning {self.chain} for high-volume MEV targets...")
        discovered_tokens = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                # We do a broad search, and filter results by chain
                async with session.get(self.dexscreener_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get("pairs", [])
                        
                        # Filter for our target chain and valid pairs
                        chain_pairs = [p for p in pairs if p.get("chainId") == self.chain]
                        
                        # Sort by volume (24h)
                        chain_pairs.sort(key=lambda x: x.get("volume", {}).get("h24", 0), reverse=True)
                        
                        for pair in chain_pairs:
                            base_token = pair.get("baseToken", {})
                            quote_token = pair.get("quoteToken", {})
                            
                            # We usually want pairs against USDC or WETH. Let's look for tokens paired with USDC
                            if quote_token.get("symbol") == "USDC" or base_token.get("symbol") == "USDC":
                                target = base_token if quote_token.get("symbol") == "USDC" else quote_token
                                symbol = target.get("symbol")
                                address = target.get("address")
                                
                                # Ignore standard stablecoins/wrapped natives to find actual volatile assets
                                if symbol not in ["USDC", "USDT", "DAI", "WMATIC", "WETH", "WBTC"]:
                                    if symbol not in discovered_tokens:
                                        discovered_tokens[symbol] = Web3.to_checksum_address(address)
                                        
                            if len(discovered_tokens) >= max_tokens:
                                break
                                
        except Exception as e:
            print(f"⚠️ [Token Discoverer] Error discovering tokens: {e}")
            
        # Fallback to defaults if API fails or rate limited
        if not discovered_tokens:
            print("⚠️ [Token Discoverer] API returned no new targets. Falling back to default high-volatility targets.")
            discovered_tokens = {
                "LINK": Web3.to_checksum_address("0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39"),
                "UNI": Web3.to_checksum_address("0xb33EaAd8d922B1083446DC23f610c2567fB5180f")
            }
            
        print(f"✅ [Token Discoverer] Locked onto {len(discovered_tokens)} new targets:")
        for sym, addr in discovered_tokens.items():
            print(f"  🎯 {sym}: {addr}")
            
        return discovered_tokens

if __name__ == "__main__":
    if __import__('os').name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    discoverer = TokenDiscoverer()
    asyncio.run(discoverer.discover_top_tokens(5))
