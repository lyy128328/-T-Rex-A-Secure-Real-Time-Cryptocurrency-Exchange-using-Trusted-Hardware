from Transaction import Transaction


class BTCToken:

    def __init__(self, address="", deposit_tx_id=""):
        self.depositTx = Transaction()
        self.depositTx.addressSelf = address
        self.depositTx.prevTxId = deposit_tx_id
        self.settlementTx = Transaction()
        self.kickoffTxs = []

    def __eq__(self, other):
        if not isinstance(other, BTCToken):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.depositTx == other.depositTx and self.settlementTx == other.settlementTx \
            and self.kickoffTxs == other.kickoffTxs

    def __str__(self):
        return "BTC Token: {deposit_tx_id: " + self.depositTx.prevTxId + ", initial_owner: " + self.depositTx.addressSelf + \
               ", settlement_tx_id: " + self.settlementTx.prevTxId + "}"
