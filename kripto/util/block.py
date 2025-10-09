import hashlib
import time
import json
from utils import generate_merkle_root

class Block:
    def __init__(self, number, prev_hash, transactions):
        self.number = number
        self.prev_hash = prev_hash
        self.merkle_root = generate_merkle_root(transactions)
        self.timestamp = time.time()
        self.nonce = 0
        self.transactions = transactions

    def calculate_hash(self):
        block_dict = {
            "number": self.number,
            "prev_hash": self.prev_hash,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_dict, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def validate(self, difficulty=5):
        prefix = '0' * difficulty
        return self.calculate_hash().startswith(prefix)

    def mine(self, difficulty=5):
        prefix = '0' * difficulty
        while True:
            hash_result = self.calculate_hash()
            if hash_result.startswith(prefix):
                return hash_result
            self.nonce += 1

    def show_block(self, only_Header=False):
        print(f"Block Number: {self.number}")
        print(f"Previous Block Hash: {self.prev_hash}")
        print(f"Merkle Root: {self.merkle_root}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Nonce: {self.nonce}")
        if not only_Header:
            print(f"Self Hash: {self.calculate_hash()}")
            print("Transactions:")
            for tx in self.transactions:
                print("---------------")
                tx.show_transaction()
            print("\n")