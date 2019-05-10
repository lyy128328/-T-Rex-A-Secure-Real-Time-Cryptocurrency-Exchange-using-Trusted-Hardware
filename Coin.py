class Coin:

    def __init__(self, globalCoinId, nonce=0, coinVal=0.0):
        self.globalCoinId = globalCoinId
        self.nonce = nonce
        self.coinVal = coinVal

    def __eq__(self, other):
        if not isinstance(other, Coin):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.globalCoinId == other.globalCoinId and self.nonce == other.nonce and self.coinVal == other.coinVal
