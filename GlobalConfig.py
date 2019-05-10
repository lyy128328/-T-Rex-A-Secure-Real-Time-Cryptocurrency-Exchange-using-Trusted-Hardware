import base58

MODE = 1    # 1 = test for latency, 2 = test for throughput
TRex_ETH_ADDRESS = "0x4dfb5bc94514a0f196037f9437f18812b80c10a0"
TRex_BTC_ADDRESS = "1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX"
TRex_HASHED_PUBLIC_KEY = base58.b58decode_check(TRex_BTC_ADDRESS)[1:].hex()
TRex_SECRET_KEY = "CF933A6C602069F1CBC85990DF087714D7E86DF0D0E48398B7D8953E1F03534A"
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)