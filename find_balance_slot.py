import os
import asyncio
import aiohttp
from web3 import Web3
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    w3 = Web3()
    pool = '0x853Ee4b2A13f8a742d64C8F088bE7bA2131f670d'
    weth = '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'
    
    slots = []
    # Test common mapping slots (0 to 10)
    for i in range(11):
        slot = w3.keccak(hexstr=pool.replace('0x', '').zfill(64) + hex(i)[2:].zfill(64)).hex()
        slots.append({'jsonrpc':'2.0','method':'eth_getStorageAt','params':[weth, slot, 'latest'],'id':i, 'mapped_slot': slot})
        
    async with aiohttp.ClientSession() as session:
        async with session.post('https://polygon-bor.publicnode.com', json=slots) as resp:
            data = await resp.json()
            for i, r in enumerate(data):
                if r['result'] != '0x0000000000000000000000000000000000000000000000000000000000000000':
                    print(f"Match found at base slot {i}: Mapped Slot = {slots[i]['mapped_slot']}")
                    print(f"Value: {r['result']}")
                    # Verify if it matches USDC reserve
                    val_int = int(r['result'], 16)
                    print(f"Int Value: {val_int}")

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
