from Transaction import Transaction


class ETHToken:

    def __init__(self, address="", deposit_tx_id=""):
        self.depositTx = Transaction()
        self.depositTx.addressSelf = address
        self.depositTx.prevTxId = deposit_tx_id
        self.coins = []
        self.v = ""
        self.r = ""
        self.s = ""
        self.hash = ""

    def __eq__(self, other):
        if not isinstance(other, ETHToken):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.depositTx == other.depositTx and self.coins == other.coins and self.v == other.v \
            and self.r == other.r and self.s == other.s and self.hash == other.hash

    def __str__(self):
        return "ETH Token: {deposit_tx_id: " + self.depositTx.prevTxId + ", initial_owner: " + self.depositTx.addressSelf + \
               ", v: " + self.v + ", r: " + self.r + ", s: " + self.s + ", hash: " + self.hash + "}"
