import asyncio
import aiohttp
from web3 import Web3

w3 = Web3()

async def main():
    USDC = Web3.to_checksum_address('0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174')
    WETH = Web3.to_checksum_address('0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619')
    
    QS_FACTORY_ABI = [{'constant':True,'inputs':[{'internalType':'address','name':'','type':'address'},{'internalType':'address','name':'','type':'address'}],'name':'getPair','outputs':[{'internalType':'address','name':'','type':'address'}],'payable':False,'stateMutability':'view','type':'function'}]
    
    qs_factory = w3.eth.contract(address=Web3.to_checksum_address('0x5757371414417b8C6c015CACea795d2c2Ac8A1E7'), abi=QS_FACTORY_ABI)
    calldata = qs_factory.encode_abi('getPair', args=[USDC, WETH])
    
    payload = {
        'jsonrpc': '2.0',
        'method': 'eth_call',
        'params': [{'to': '0x5757371414417b8C6c015CACea795d2c2Ac8A1E7', 'data': calldata}, 'latest'],
        'id': 1
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post('https://polygon-bor.publicnode.com', json=payload) as resp:
            print(await resp.json())

if __name__ == '__main__':
    import os
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
