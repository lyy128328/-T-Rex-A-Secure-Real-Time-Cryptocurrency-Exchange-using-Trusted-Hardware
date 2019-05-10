import socket, pickle
import urllib.request, json
from BTCToken import BTCToken
from ETHToken import ETHToken
import GlobalConfig


class Request:

    def __init__(self, buyCoin, sellCoin, buyVol, sellVol, trader_sell, trader_buy, token):
        self.buyCurrency = buyCoin
        self.sellCurrency = sellCoin
        if self.buyCurrency == self.sellCurrency:
            raise ValueError("Your buy currency cannot be the same as sell currency!")
        self.buyVolume = buyVol
        self.sellVolume = sellVol
        self.sellAddress = trader_sell
        self.buyAddress = trader_buy
        self.token = token

    def __eq__(self, other):
        if not isinstance(other, Request):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.buyCurrency == other.buyCurrency and self.sellCurrency == other.sellCurrency and \
            self.buyVolume == other.buyVolume and self.sellVolume == other.sellVolume and \
            self.sellAddress == other.sellAddress and self.buyAddress == self.buyAddress and self.token == other.token

    def __str__(self):
        return "{buy_coin: " + self.buyCurrency + ", sell_coin: " + self.sellCurrency + \
               ", buy_vol: " + str(self.buyVolume) + ", sell_vol: " + str(self.sellVolume) + \
               ", pk_hash_buy: " + self.buyAddress + ", pk_hash_sell: " + self.sellAddress + \
               ", deposit_tx_id: " + self.token.depositTx.prevTxId + "}"

btc_to_eth_requests = []
eth_to_btc_requests = []

# get sample txid and pkhash data from BTC blockchain
contents = urllib.request.urlopen("https://blockchain.info/unconfirmed-transactions?format=json").read()
contents_obj = json.loads(contents)
ethBTCRatio = .033
for i in range(100):
    if i >= len(contents_obj["txs"]):
        trader = btc_to_eth_requests[i%10].sellAddress
        depositTxId = btc_to_eth_requests[i%10].token.depositTx.prevTxId
        new_token = BTCToken(trader, depositTxId)
        new_token.depositTx.addressMatch = GlobalConfig.TRex_BTC_ADDRESS
        # TODO: In reality these addresses should be different (BTC vs ETH)
        new_request = Request("ETH", "BTC", ethBTCRatio * (i+1), i+1, trader, trader, new_token)
    else:
        tx = contents_obj["txs"][i]
        trader = tx["inputs"][0]["prev_out"]["addr"]
        depositTxId = tx["hash"]
        new_token = BTCToken(trader,depositTxId)
        new_token.depositTx.addressMatch = GlobalConfig.TRex_BTC_ADDRESS
        # TODO: In reality these addresses should be different (BTC vs ETH)
        new_request = Request("ETH", "BTC", ethBTCRatio * (i+1), i+1, trader, trader, new_token)
    btc_to_eth_requests.append(new_request)

'''print("BTC -> ETH Requests----------------------------")
for request in btc_to_eth_requests:
    print(request)'''

# get sample txid and pkhash data from ETH blockchain
contents = urllib.request.urlopen("https://api.blockcypher.com/v1/eth/main/txs").read()
contents_obj = json.loads(contents)
for i in range(100):
    if i >= len(contents_obj):
        trader = eth_to_btc_requests[i%10].sellAddress
        depositTxId = eth_to_btc_requests[i%10].token.depositTx.prevTxId
        new_token = ETHToken(trader, depositTxId)
        new_token.depositTx.addressMatch = GlobalConfig.TRex_ETH_ADDRESS
        # TODO: In reality these addresses should be different (BTC vs ETH)
        new_request = Request("BTC", "ETH", i+1, ethBTCRatio * (i+1), trader, trader, new_token)
    else:
        tx = contents_obj[i]
        trader = tx["addresses"][0]
        depositTxId = tx["hash"]
        new_token = ETHToken(trader,depositTxId)
        new_token.depositTx.addressMatch = GlobalConfig.TRex_ETH_ADDRESS
        # TODO: In reality these addresses should be different (BTC vs ETH)
        new_request = Request("BTC","ETH", i+1, ethBTCRatio * (i+1), trader, trader, new_token)
    eth_to_btc_requests.append(new_request)

'''print("ETH-> BTC Requests----------------------------")
for request in eth_to_btc_requests:
    print(request)'''

# WE NOW HAVE A LIST OF 100 REQUESTS FROM BOTH SIDES -> SEND OVER SOCKET

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((GlobalConfig.HOST, GlobalConfig.PORT))
    for request in btc_to_eth_requests+eth_to_btc_requests:
        req_str = pickle.dumps(request)
        client.sendall(req_str)
        data = client.recv(1024)
        data_str = pickle.loads(data)
        #if data_str.split("/")[0] == "depositToken":
        print("Deposit token received for trader: " + data_str.split("/")[1])
        #else:
            #print("Deposit token not received for trader: " + request.sellAddress)

    client.sendall(pickle.dumps("requestsFinished"))

    while True:
        data = client.recv(1024)
        if not data:
            print("Connection closed abruptly.")
            break
        data_str = pickle.loads(data)
        if data_str == "closeChannel":
            print("Connection closed.")
            break
        elif data_str.split("/")[0] == "depositToken":
            print("Deposit token received for trader: " + data_str.split("/")[1])
        elif data_str.split("/")[0] == "confirmMatch":
            client.sendall(pickle.dumps("accept"))
        elif data_str.split("/")[0] == "swapToken":
            client.sendall(pickle.dumps("ACK"))

client.close()
