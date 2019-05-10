import socket,pickle,copy
import GlobalConfig
from Transaction import Transaction
from BTCToken import BTCToken
from ETHToken import ETHToken
from Coin import Coin
from multiprocessing.dummy import Pool as ThreadPool
import socket
import time
import numpy
import threading


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


class TRexServer:

    def __init__(self, host, port, N, locktime_interval, end_of_exchange, end_of_settlement):
        self.host = host
        self.port = port
        if host == "" or port == "":
            raise Exception("You must specify a host and port!")
        self.N = N
        self.locktime_interval = locktime_interval
        self.end_of_exchange = end_of_exchange
        self.end_of_settlement = end_of_settlement
        self.pending_requests = []
        self.btc_valid_tokens = {}  # BTC dict: user address -> valid BTCTokens
        self.global_coin_id = 0 # global coin ID for ETH
        self.eth_valid_tokens = {}  # ETH dict: user address -> valid ETHTokens
        self.connection = None
        self.socket = None
        self.trades_completed = 0
        # timing the latency
        self.latencies = []
        self.socketLock = None
        self.enclaveLock = None

    def start_server(self):
        # TODO: Test latency -> send 200 requests (100 each side), process one-by-one, time each and take average
        # TODO: Test throughput -> multithread, send 10k requests, time whole batch, divide by time to get # in 1 min
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = s
        s.bind((self.host, self.port))
        s.listen()
        while True:
            conn, addr = s.accept()
            self.connection = conn
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                request_str = pickle.loads(data)
                if request_str == "requestsFinished":
                    break
                # SIMULATING THE DEPOSITS PURELY FOR TESTING PURPOSES
                self.deposit(request_str.sellCurrency,request_str.sellAddress, request_str.token, request_str.sellVolume)
                # validate the request -> must supply correct token
                if request_str.sellCurrency == "BTC":
                    if request_str.sellAddress not in self.btc_valid_tokens:
                        print("Owner for given BTC request does not have a token to use.")
                    elif request_str.token not in self.btc_valid_tokens[request_str.sellAddress]:
                        print("Owner for given BTC request did not provide a valid token.")
                    else:
                        self.pending_requests.append(request_str)
                elif request_str.sellCurrency == "ETH":
                    if request_str.sellAddress not in self.eth_valid_tokens:
                        print("Owner for given ETH request does not have a token to use.")
                    elif request_str.token not in self.eth_valid_tokens[request_str.sellAddress]:
                        print("Owner for given ETH request did not provide a valid token.")
                        print(request_str.token)
                        print(self.eth_valid_tokens[request_str.sellAddress][-1])
                    else:
                        self.pending_requests.append(request_str)
                #print("Data received:", request_str)
                #conn.sendall(data)
            self.run_exchange()
            self.close_server()
            break

    def close_server(self):
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()

    def deposit(self, currency, user_addr, deposit_token, val=0):
        if currency == "BTC":
            if isinstance(deposit_token,BTCToken):
                if user_addr in self.btc_valid_tokens:
                    self.btc_valid_tokens[user_addr].append(deposit_token)
                else:
                    self.btc_valid_tokens[user_addr] = [deposit_token]
                self.send_deposit_token(user_addr, deposit_token)
            else:
                raise ValueError("Provided deposit token is not a BTCToken")
        elif currency == "ETH":
            if isinstance(deposit_token,ETHToken):
                for i in range(self.N):
                    self.global_coin_id += 1
                    new_coin = Coin(self.global_coin_id, 0, (val/self.N))
                    deposit_token.coins.append(new_coin)
                if user_addr in self.eth_valid_tokens:
                    self.eth_valid_tokens[user_addr].append(deposit_token)
                else:
                    self.eth_valid_tokens[user_addr] = [deposit_token]
                self.send_deposit_token(user_addr, deposit_token)
            else:
                ValueError("Provided deposit token is not a ETHToken")

    def send_deposit_token(self, trader, token):
        self.connection.sendall(pickle.dumps("depositToken/" + trader + "/" + str(token)))

    def settlement(self):
        self.btc_valid_tokens = {}
        self.eth_valid_tokens = {}
        self.pending_requests = []

    def confirm_match_with_trader(self, trader, request):
        with self.socketLock:
            self.connection.sendall(pickle.dumps("confirmMatch/" + trader + "/" + str(request)))
            while True:
                data = self.connection.recv(1024)
                if not data:
                    break
                request_str = pickle.loads(data)
                if request_str == "accept":
                    return "accept"
                elif request_str == "reject":
                    return "reject"

            print("An error occurred when confirming the match with trader: " + trader)
            return "reject"

    def match(self):
        current_req = self.pending_requests.pop()
        foundMatch = False
        # simple request matching -> real exchange would be more complex
        for index, req in enumerate(self.pending_requests):
            if current_req.buyCurrency == req.sellCurrency and current_req.sellCurrency == req.buyCurrency and \
                    current_req.buyVolume == req.sellVolume and current_req.sellVolume == req.buyVolume:
                foundMatch = True
                if self.confirm_match_with_trader(req.sellAddress, current_req) == "accept" and \
                        self.confirm_match_with_trader(current_req.sellAddress, req) == "accept":
                    self.pending_requests.pop(index)
                    if current_req.sellCurrency == "BTC":
                        start = time.time()
                        self.micro_exchange(current_req, req)
                        end = time.time()
                        self.latencies.append(end - start)
                    else:
                        start = time.time()
                        self.micro_exchange(req, current_req)
                        end = time.time()
                        self.latencies.append(end - start)
                    break
                else:
                    foundMatch = False
                    continue

        if not foundMatch:
            self.pending_requests = [current_req] + self.pending_requests

    def threaded_match(self, current_req):
        # simple request matching -> real exchange would be more complex
        for index, req in enumerate(self.pending_requests[100:]):
            if req == current_req:
                continue
            if current_req.buyCurrency == req.sellCurrency and current_req.sellCurrency == req.buyCurrency and \
                    current_req.buyVolume == req.sellVolume and current_req.sellVolume == req.buyVolume:
                if self.confirm_match_with_trader(req.sellAddress, current_req) == "accept" and \
                        self.confirm_match_with_trader(current_req.sellAddress, req) == "accept":
                    if current_req.sellCurrency == "BTC":
                        self.micro_exchange(current_req, req)
                    else:
                        self.micro_exchange(req, current_req)
                    break
                else:
                    continue

    def run_exchange(self):
        # One-by-one mode (test for latency)
        if GlobalConfig.MODE == 1:
            self.socketLock = threading.Lock()
            self.enclaveLock = threading.Lock()
            while len(self.pending_requests) > 0:
                self.match()
            latency_avg = numpy.mean(self.latencies)
            print('Number of latencies: ' + str(len(self.latencies)))
            print('Avarage Latency: ' + str(latency_avg) + 'seconds')
        # Concurrent multithreading mode (test for throughput)
        elif GlobalConfig.MODE == 2:
            pool = ThreadPool(10)
            queue = copy.copy(self.pending_requests)[:100]
            self.socketLock = threading.Lock()
            self.enclaveLock = threading.Lock()
            pool.map(self.threaded_match, queue)
            pool.close()
            pool.join()

        else:
            print("Mode not set correctly in Global Config.")

        self.settlement()
        self.connection.sendall(pickle.dumps("closeChannel"))

    def enclave_microswap(self, prevTxId, addressSelf, addressMatch, valToSelf, valToMatch, timeLock):
        # TODO: Fix params and implement
        # call the C++ microswap script in here -> runs in enclave
        # should return the tx hex
        #print("in enclave_microswap")
        # simply concact it to a string for now, need modification
        message = prevTxId + addressSelf + addressMatch + str(valToSelf) + str(valToMatch) + str(timeLock)
        with self.enclaveLock:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 5537))
            client.send(message.encode())
            #time.sleep(0.2)
            tx = client.recv(1024).decode()
            print ('Received message:', tx)
            client.close()
            return tx

    def enclave_kickoff(self, prevTxId, valToMatch, timeLock):
        # TODO: Fix params and implement
        # call the C++ kickoff script in here -> runs in enclave
        # should return the tx hex
        #print("in enclave_kickoff")
        # simply concact it to a string for now, need modification
        message = prevTxId + str(valToMatch) + str(timeLock)
        with self.enclaveLock:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 5537))
            client.send(message.encode())
            #time.sleep(0.2)
            tx = client.recv(1024).decode()
            print ('Received message:', tx)
            client.close()
            return tx

    def broadcast_kickoff(self):
        # TODO: Fix params and implement
        # spend kickoff tx by broadcasting to BTC chain
        # should return tx id
        return ""

    def enclave_eth_signing(self, prevTxId, addressSelf, nonce):
        # TODO: Fix params and implement
        # call the C++ ETH message signing script in here -> runs in enclave
        # should return v,r,s and hash
        #print("in enclave_eth_signing")
        # simply concact it to a string for now, need modification
        message = prevTxId + str(addressSelf) + str(nonce)
        with self.enclaveLock:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 5537))
            client.send(message.encode())
            #time.sleep(0.2)
            tx = client.recv(1024).decode()
            print ('Received message:', tx)
            client.close()
            return tx,"","",""

    def confirm_token_with_trader(self, trader, token):
        with self.socketLock:
            self.connection.sendall(pickle.dumps("swapToken/" + trader + "/" + str(token)))
            while True:
                data = self.connection.recv(1024)
                if not data:
                    break
                request_str = pickle.loads(data)
                if request_str == "ACK":
                    return "ACK"
                else:
                    print("An error occurred when sending the microswap token to trader: " + trader)
                    return "error"

        print("An error occurred when sending the microswap token to trader: " + trader)
        return "error"

    def micro_exchange(self, request1, request2):

        # request1 -> Buy ETH, Sell BTC
        # request2 -> Buy BTC, Sell ETH

        token1 = request1.token
        token2 = request2.token

        for i in range(self.N):
            # BTC Microswap
            if token1.settlementTx.addressSelf == "":
                token1.settlementTx.addressSelf = request1.sellAddress
                token1.settlementTx.addressMatch = request2.buyAddress
                token1.settlementTx.valToMatch = i*(request1.sellVolume/self.N)
                token1.settlementTx.valToSelf = request1.sellVolume - token1.settlementTx.valToMatch
                token1.settlementTx.timeLock = self.end_of_settlement - self.locktime_interval
                token1.settlementTx.prevTxId = token1.depositTx.prevTxId
                # TODO: Fix this
                token1.settlementTx.txHash = self.enclave_microswap(token1.settlementTx.prevTxId, token1.settlementTx.addressSelf, token1.settlementTx.addressMatch, token1.settlementTx.valToSelf, token1.settlementTx.valToMatch, token1.settlementTx.timeLock)
            else:
                token1.settlementTx.valToMatch = i * (request1.sellVolume / self.N)
                token1.settlementTx.valToSelf = request1.sellVolume - token1.settlementTx.valToMatch
                if token1.settlementTx.timeLock - self.locktime_interval > self.end_of_exchange:
                    token1.settlementTx.timeLock -= self.locktime_interval
                else:
                    if len(token1.kickoffTxs) == 0:
                        new_kickoff_tx = Transaction()
                        new_kickoff_tx.addressSelf = token1.depositTx.addressMatch
                        new_kickoff_tx.valToSelf = 0
                        new_kickoff_tx.addressMatch = token1.depositTx.addressMatch
                        new_kickoff_tx.valToMatch = token1.depositTx.valToMatch
                        new_kickoff_tx.timeLock = 0
                        new_kickoff_tx.prevTxId = token1.depositTx.prevTxId
                        # TODO: Fix this
                        new_kickoff_tx.txHash = self.enclave_kickoff(new_kickoff_tx.prevTxId, new_kickoff_tx.valToMatch, self.end_of_settlement - self.locktime_interval)
                        # TODO: Fix this
                        # TODO: Fix this
                        new_kickoff_tx.prevTxId = self.broadcast_kickoff()
                        token1.kickoffTxs.append(new_kickoff_tx)
                        token1.settlementTx.prevTxId = new_kickoff_tx.prevTxId
                        token1.settlementTx.timeLock = self.end_of_settlement - self.locktime_interval
                    else:
                        new_kickoff_tx = Transaction()
                        last_kickoff_tx = copy.copy(token1.kickoffTxs[-1])
                        new_kickoff_tx.addressSelf = last_kickoff_tx.addressMatch
                        new_kickoff_tx.valToSelf = 0
                        new_kickoff_tx.addressMatch = last_kickoff_tx.addressMatch
                        new_kickoff_tx.valToMatch = last_kickoff_tx.valToMatch
                        new_kickoff_tx.timeLock = 0
                        new_kickoff_tx.prevTxId = last_kickoff_tx.prevTxId
                        # TODO: Fix this
                        new_kickoff_tx.txHash = self.enclave_kickoff(new_kickoff_tx.prevTxId, new_kickoff_tx.valToMatch, self.end_of_settlement - self.locktime_interval)
                        # TODO: Fix this
                        # TODO: Fix this
                        new_kickoff_tx.prevTxId = self.broadcast_kickoff()
                        token1.kickoffTxs.append(new_kickoff_tx)
                        token1.settlementTx.prevTxId = new_kickoff_tx.prevTxId
                        token1.settlementTx.timeLock = self.end_of_settlement - self.locktime_interval

            # ETH Microswap
            if i == 0:
                split_token = ETHToken(token2.depositTx.addressSelf,token2.depositTx.prevTxId)
            else:
                split_token = copy.copy(self.eth_valid_tokens[request1.buyAddress][-1])
            split_coin = copy.copy(token2.coins[0])
            split_coin.nonce += 1
            split_token.coins.append(split_coin)
            token2.coins.pop(0)
            # TODO: Fix this
            _hash,_v,_r,_s = self.enclave_eth_signing(split_token.depositTx.prevTxId, split_token.depositTx.addressSelf, split_coin.nonce)
            split_token.hash = _hash
            split_token.v = _v
            split_token.r = _r
            split_token.s = _s

            # token 1 internal change of hands (BTC)
            #self.btc_valid_tokens[request1.sellAddress].remove(token1)
            if request2.buyAddress in self.btc_valid_tokens:
                self.btc_valid_tokens[request2.buyAddress].append(token1)
            else:
                self.btc_valid_tokens[request2.buyAddress] = [token1]
            if i == self.N - 1:
                # token 2 internal change of hands (ETH)
                #self.eth_valid_tokens[request2.sellAddress].remove(token2)
                if request1.buyAddress in self.eth_valid_tokens:
                    self.eth_valid_tokens[request1.buyAddress].append(token2)
                else:
                    self.eth_valid_tokens[request1.buyAddress] = [token2]
            else:
                if request1.buyAddress in self.eth_valid_tokens:
                    self.eth_valid_tokens[request1.buyAddress].append(split_token)
                else:
                    self.eth_valid_tokens[request1.buyAddress] = [split_token]

            # send tokens, handle case when at least one part doesn't ACK
            if self.confirm_token_with_trader(request2.buyAddress,token1) == "ACK" and \
                    self.confirm_token_with_trader(request1.buyAddress,split_token) == "ACK":
                if i == self.N-1:
                    self.trades_completed += 1
                    print("# Trades Completed: ", self.trades_completed)
                    #print("TRADE COMPLETED, # REMAINING IN QUEUE: ", len(self.pending_requests) / 2)

            else:
                print("Microswap terminated with {0} swaps left due to party inactivity.".format(self.N - i))
                return


if __name__ == '__main__':
    # TEST PARAMS
    test_host = GlobalConfig.HOST
    test_port = GlobalConfig.PORT
    N = 10
    locktime_interval = 1
    end_of_exchange = 10
    end_of_settlement = 5
    test_server = TRexServer(test_host,test_port,N,locktime_interval,end_of_exchange,end_of_settlement)
    # test throughtput
    start = time.time()
    test_server.start_server()
    end = time.time()
    #print('Throughtput Time: ' + str(end - start) + 'seconds')