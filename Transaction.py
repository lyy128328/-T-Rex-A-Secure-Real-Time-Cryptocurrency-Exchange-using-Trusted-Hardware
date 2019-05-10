class Transaction:

    def __init__(self):
        self.addressSelf = ""
        self.valToSelf = 0
        self.addressMatch = ""
        self.valToMatch = 0
        self.timeLock = 0
        self.prevTxId = ""
        self.txHash = ""

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.addressSelf == other.addressSelf and self.valToSelf == other.valToSelf \
            and self.addressMatch == other.addressMatch and self.valToMatch == other.valToMatch and \
            self.timeLock == other.timeLock and self.prevTxId == other.prevTxId and self.txHash == other.txHash
