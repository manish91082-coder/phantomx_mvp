import os
import asyncio
import aiohttp
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    pool_address = '0x853Ee4b2A13f8a742d64C8F088bE7bA2131f670d'
    payload = [{'jsonrpc':'2.0','method':'eth_getStorageAt','params':[pool_address, hex(i), 'latest'],'id':i} for i in range(15)]
    async with aiohttp.ClientSession() as session:
        async with session.post('https://polygon-bor.publicnode.com', json=payload) as resp:
            data = await resp.json()
            for r in data: 
                print(f"Slot {r['id']}: {r['result']}")

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
