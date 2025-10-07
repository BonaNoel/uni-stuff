import hashlib
import json


class Transaction:
    def __init__(self, sender, receiver, amount, signature):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.signature = signature

    def calculate_hash(self):
        transaction_dict = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "signature": self.signature,
        }
        transaction_string = json.dumps(transaction_dict, sort_keys=True)
        return hashlib.sha256(transaction_string.encode()).hexdigest()
