from celo_sdk.kit import Kit
from pycoingecko import CoinGeckoAPI
import aiohttp
import asyncio
import json
import time

from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

ether = 1000000000000000000

with open("./abis/IPriceOracleGetter.json") as f:
    IPrice_Oracle_Getter = json.load(f)  

cg = CoinGeckoAPI()
coin_dict = {
"cusd": "cUSD",
"celo": "Celo",
"ceuro": "cEUR"
}

kit = Kit('https://forno.celo.org')
web3 = kit.w3
eth = web3.eth
helper_w3 = Kit('https://forno.celo.org').w3

def get_latest_block(celo_mainnet_web3): 
    celo_mainnet_web3.middleware_onion.clear()
    blocksLatest = celo_mainnet_web3.eth.getBlock("latest")
    return int(blocksLatest["number"], 16)    

coins_reserve_address = {
         "celo": '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
         "cusd": '0x765DE816845861e75A25fCA122bb6898B8B1282a' , 
         "ceuro": '0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73'  
}

price_oracle = eth.contract(address='0x568547688121AA69bDEB8aEB662C321c5D7B98D0', abi= IPrice_Oracle_Getter)

def get_price_in_celo(coin_name, coin_address):
    return (price_oracle.functions.getAssetPrice(coin_address).call()/ether)

def get_exchange_rate_in_usd(coin_name, coin_address):
    price_in_celo = get_price_in_celo(coin_name, coin_address)
    return price_in_celo, price_in_celo*cg.get_price(ids='celo', vs_currencies='usd')['celo']['usd']
 
URL = "http://moola-downstream-api.herokuapp.com/"

async def fetch(session, url, params):
    async with session.get(url, params=params) as response:
        resp = await response.json()
        print(resp)
        if (resp["status"] == "OK"):
            print("The request was a success!")
        # else:
        #     response.raise_for_status()
        return resp    

async def fetch_all(exchange_rate_reqs):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for exchange_rate_req in exchange_rate_reqs:
            tasks.append(
                fetch(
                    session,
                    exchange_rate_req["url"],
                    exchange_rate_req["params"],
                )
            )
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        # return responses

def dump_data(api_url, params, method):
    asyncio.run(fetch(URL+api_url, params, method))

def dump_coin_exchange_rate(coinName, network, usd_exchange_rate, celo_exchange_rate, cusd_exchange_rate, ceuro_exchange_rate, block_number):
    return URL+'set/insert/db_celo_mainnet/tbl_coin_exchange_rate', {'coin_name': coin_dict[coinName], 'network_name': network, 'usd_exchange_rate': usd_exchange_rate, "celo_exchange_rate":celo_exchange_rate, "cusd_exchange_rate":cusd_exchange_rate, "ceuro_exchange_rate":ceuro_exchange_rate, 'agent_id':0, 'block_number': block_number, "block_number__Type": "int"}, 'GET'


@sched.scheduled_job('interval', seconds=30)
def timed_job():
    celo_mainnet_latest_block = get_latest_block(helper_w3)
    exchange_rate_reqs = []
    celo_usd, cusd_usd, ceuro_usd = get_exchange_rate_in_usd("celo", coins_reserve_address["celo"]), get_exchange_rate_in_usd("cusd", coins_reserve_address["cusd"]),get_exchange_rate_in_usd("ceuro", coins_reserve_address["ceuro"])
    cusd_in_celo, ceuro_in_celo = get_price_in_celo("cusd", coins_reserve_address["cusd"]), get_price_in_celo("ceuro", coins_reserve_address["ceuro"])

    url, params, method = dump_coin_exchange_rate('celo', 'celo mainnet',  celo_usd, 1, 1/cusd_in_celo, 1/ceuro_in_celo,celo_mainnet_latest_block)
    exchange_rate_reqs.append({"url": url, "params": params, "method": method})
        
    url, params, method = dump_coin_exchange_rate('cusd', 'celo mainnet',  cusd_usd, cusd_in_celo, 1, cusd_in_celo/ceuro_in_celo,celo_mainnet_latest_block)
    exchange_rate_reqs.append({"url": url, "params": params, "method": method})

    url, params, method = dump_coin_exchange_rate('ceuro', 'celo mainnet',  ceuro_usd, ceuro_in_celo, ceuro_in_celo/cusd_in_celo, 1,celo_mainnet_latest_block)
    exchange_rate_reqs.append({"url": url, "params": params, "method": method})

   
    asyncio.run(fetch_all(exchange_rate_reqs))

sched.start()



    

